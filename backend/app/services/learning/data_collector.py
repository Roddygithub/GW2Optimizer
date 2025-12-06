"""Data collection service for learning system."""

# Standard library imports
import json
import logging
import os
import time
import uuid
import zlib
from datetime import datetime as datetime_type
from collections import defaultdict
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Third-party imports
from prometheus_client import Counter, Gauge, Histogram, start_http_server

# Local application imports
from app.models.build import Build, GameMode, Profession, Role
from app.models.learning import DataSource, TrainingDatapoint
from app.models.team import TeamComposition

# Configure logging
logger = logging.getLogger(__name__)

# Taille maximale du cache en nombre d'éléments
MAX_CACHE_SIZE = 1000


class DataCollector:
    """Service for collecting and storing training data with monitoring."""
    
    # Metrics
    _metrics_initialized = False
    
    # Collection metrics
    collect_requests = Counter(
        'datacollector_collect_requests_total', 
        'Total number of collection requests',
        ['type']  # build, team, meta_build
    )
    
    collect_errors = Counter(
        'datacollector_collect_errors_total',
        'Total number of collection errors',
        ['type', 'error']  # type: build/team/meta_build, error: validation/io/etc.
    )
    
    collect_duration = Histogram(
        'datacollector_collect_duration_seconds',
        'Time spent collecting data',
        ['type']
    )
    
    # Cache metrics
    cache_hits = Counter(
        'datacollector_cache_hits_total',
        'Total number of cache hits',
        ['operation']  # load_datapoint, get_all_datapoints
    )
    
    cache_misses = Counter(
        'datacollector_cache_misses_total',
        'Total number of cache misses',
        ['operation']
    )
    
    # Storage metrics
    datapoints_count = Gauge(
        'datacollector_datapoints_total',
        'Total number of datapoints stored'
    )
    
    storage_size = Gauge(
        'datacollector_storage_size_bytes',
        'Total size of stored data in bytes'
    )
    
    # Performance metrics
    operation_duration = Histogram(
        'datacollector_operation_duration_seconds',
        'Duration of operations',
        ['operation']  # store_datapoint, load_datapoint, etc.
    )
    
    def __init__(self, storage_path: Optional[Union[str, Path]] = None, metrics_port: int = 9000):
        """Initialize the data collector.

        Args:
            storage_path: Path to store the training data. Defaults to 'training_data' in the current directory.
            metrics_port: Port to expose Prometheus metrics on. If None, metrics server won't be started.
        """
        self.storage_path = Path(storage_path) if storage_path else Path("training_data")
        self.datapoints_file = self.storage_path / "datapoints.jsonl"
        
        # Initialize metrics if not already done
        if not DataCollector._metrics_initialized and metrics_port is not None:
            self._init_metrics(metrics_port)
        
        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache for metadata
        self._metadata_cache = {}
        self._metadata_loaded = False
        
        # Performance tracking
        self._operation_times = defaultdict(list)
        
        # Update metrics
        self._update_storage_metrics()
    
    @classmethod
    def _init_metrics(cls, port: int):
        """Initialize Prometheus metrics server."""
        if cls._metrics_initialized:
            return
            
        try:
            # Try to start the server
            try:
                start_http_server(port)
                logger.info(f"Started metrics server on port {port}")
                cls._metrics_initialized = True
            except OSError as e:
                if "Address already in use" in str(e):
                    # If port is in use, it's likely another instance is running
                    logger.warning(f"Metrics server port {port} is already in use. Using existing metrics server.")
                    cls._metrics_initialized = True
                else:
                    raise
        except Exception as e:
            logger.warning(f"Failed to start metrics server: {e}. Metrics collection will be disabled.")
            cls._metrics_initialized = False
    
    def _update_storage_metrics(self):
        """Update storage-related metrics."""
        try:
            # Count datapoints
            count = 0
            if self.datapoints_file.exists():
                with open(self.datapoints_file, 'r') as f:
                    count = sum(1 for _ in f)
            
            self.datapoints_count.set(count)
            
            # Calculate storage size
            total_size = 0
            if self.storage_path.exists():
                total_size = sum(f.stat().st_size for f in self.storage_path.glob('**/*') if f.is_file())
            
            self.storage_size.set(total_size)
            
        except Exception as e:
            logger.error(f"Error updating storage metrics: {e}")

    async def collect_build(
        self,
        build: Optional[Build],
        source: DataSource = DataSource.AI_GENERATED,
    ) -> TrainingDatapoint:
        """
        Collect a build for training.

        Args:
            build: Build to collect. Must not be None.
            source: Source of the build

        Returns:
            Created training datapoint
            
        Raises:
            ValueError: If the build is None, or if the build data is invalid or too large
        """
        # Start tracking operation time
        start_time = time.time()
        success = False

        # Increment request counter
        self.collect_requests.labels(type='build').inc()

        try:
            # Validate input
            if build is None:
                error_msg = "Build cannot be None"
                self.collect_errors.labels(type='build', error='invalid_input').inc()
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Convert build to dict and validate
            try:
                build_data = build.model_dump(mode="json")
            except AttributeError as e:
                error_msg = f"Invalid build object: {e}"
                self.collect_errors.labels(type='build', error='invalid_build').inc()
                logger.error(error_msg)
                raise ValueError(error_msg) from e

            # Sanitize input to prevent XSS and other injections
            sanitized_data = self._sanitize_input(build_data)

            # Validate data size
            if not self._validate_data_size(sanitized_data):
                error_msg = "Build data exceeds maximum allowed size"
                self.collect_errors.labels(type='build', error='data_too_large').inc()
                logger.warning(error_msg, extra={"build_id": getattr(build, 'id', None)})
                raise ValueError(error_msg)

            # Compress the data
            compressed_data = self._compress_data(sanitized_data)

            # Create a training datapoint
            try:
                datapoint = TrainingDatapoint(
                    id=str(uuid.uuid4()),
                    build_id=build.id,
                    data=sanitized_data,
                    game_mode=build.game_mode,
                    profession=build.profession if build.profession else None,
                    role=build.role if build.role else None,
                    source=source,
                    compressed_size_bytes=len(compressed_data),
                    created_at=datetime.utcnow(),
                )
            except Exception as e:
                error_msg = f"Failed to create training datapoint: {e}"
                self.collect_errors.labels(type='build', error='datapoint_creation').inc()
                logger.error(error_msg, exc_info=True)
                raise ValueError(error_msg) from e

            # Store the datapoint
            await self._store_datapoint(datapoint, compressed_data)

            # Log successful collection (used by monitoring tests)
            logger.info(
                f"Collected build {build.id}",
                extra={
                    "build_id": build.id,
                    "datapoint_id": datapoint.id,
                    "source": source,
                    "compressed_size": len(compressed_data),
                },
            )

            success = True
            return datapoint

        except ValueError as e:
            # Validation or controlled errors
            error_msg = str(e)
            logger.error(
                f"Error collecting build: {error_msg}",
                extra={
                    "build_id": getattr(build, 'id', None),
                    "error_type": "validation",
                    "error_message": error_msg,
                },
            )
            raise

        except Exception as e:
            # Handle all other exceptions
            error_type = type(e).__name__
            self.collect_errors.labels(type='build', error=error_type).inc()

            logger.error(
                f"Unexpected error collecting build: {e}",
                extra={
                    "build_id": getattr(build, 'id', None),
                    "error_type": error_type,
                    "error_message": str(e),
                },
                exc_info=True,
            )
            raise

        finally:
            # Record operation duration
            duration = time.time() - start_time
            self.collect_duration.labels(type='build').observe(duration)
            self._track_operation_time('collect_build', duration)

            # Log performance metrics
            logger.debug(
                "Build collection completed",
                extra={
                    "duration_seconds": duration,
                    "build_id": getattr(build, 'id', None) if build else None,
                    "success": success,
                },
            )

    async def collect_team(
        self,
        team: TeamComposition,
        source: DataSource = DataSource.AI_GENERATED,
    ) -> TrainingDatapoint:
        """
        Collect a team composition for training.

        Args:
            team: Team to collect
            source: Source of the team

        Returns:
            Created training datapoint
        """
        try:
            team_data = team.model_dump(mode="json")
            compressed_data = self._compress_data(team_data)

            datapoint = TrainingDatapoint(
                id=str(uuid.uuid4()),
                team_id=team.id,
                data=team_data,
                game_mode=team.game_mode,
                source=source,
                compressed_size_bytes=len(compressed_data),
            )

            # Store the datapoint
            with self.operation_duration.labels(operation='store_datapoint').time():
                await self._store_datapoint(datapoint, compressed_data)

            logger.info(f"Collected team {team.id} from {source}")
            return datapoint

        except Exception as e:
            logger.error(f"Error collecting team: {e}")
            raise

    async def collect_team_from_dict(
        self,
        team_data: Dict[str, Any],
        game_mode: str,
        source: DataSource = DataSource.AI_GENERATED,
    ) -> TrainingDatapoint:
        try:
            compressed_data = self._compress_data(team_data)

            team_id = str(team_data.get("id")) if team_data.get("id") is not None else str(uuid.uuid4())

            datapoint = TrainingDatapoint(
                id=str(uuid.uuid4()),
                team_id=team_id,
                data=team_data,
                game_mode=game_mode,
                source=source,
                compressed_size_bytes=len(compressed_data),
            )

            # Store the datapoint
            with self.operation_duration.labels(operation='store_datapoint').time():
                await self._store_datapoint(datapoint, compressed_data)

            logger.info(
                "Collected team datapoint from dict",
                extra={"team_id": datapoint.team_id, "source": source.value},
            )

            return datapoint

        except Exception as e:
            logger.error(f"Error collecting team from dict: {e}")
            raise

    async def collect_meta_build(self, meta: Dict[str, Any]) -> TrainingDatapoint:
        try:
            compressed_data = self._compress_data(meta)

            datapoint = TrainingDatapoint(
                id=str(uuid.uuid4()),
                build_id=str(meta.get("id")) if meta.get("id") is not None else None,
                data=meta,
                game_mode=str(meta.get("game_mode") or "unknown"),
                profession=meta.get("profession"),
                role=meta.get("role"),
                source=DataSource.COMMUNITY_SCRAPE,
                compressed_size_bytes=len(compressed_data),
            )

            # Store the datapoint
            with self.operation_duration.labels(operation='store_datapoint').time():
                await self._store_datapoint(datapoint, compressed_data)

            logger.info("Collected meta build", extra={"id": datapoint.build_id, "source": "community_scrape"})
            return datapoint

        except Exception as e:
            logger.error(f"Error collecting meta build: {e}")
            raise

    async def collect_advisor_decision(
        self,
        decision: Dict[str, Any],
        game_mode: str,
        profession: Optional[str] = None,
        role: Optional[str] = None,
        source: DataSource = DataSource.AI_GENERATED,
    ) -> TrainingDatapoint:
        """Collect a BuildAdvisor decision as a generic training datapoint.

        The decision payload should remain compact (scenario + quelques candidats + choix LLM)
        pour rester sous la limite de taille (~10KB) et être facilement réutilisable
        pour du few-shot ou du fine-tuning.
        """

        try:
            compressed_data = self._compress_data(decision)

            datapoint = TrainingDatapoint(
                id=str(uuid.uuid4()),
                build_id=None,
                team_id=None,
                data=decision,
                game_mode=game_mode,
                profession=profession,
                role=role,
                source=source,
                compressed_size_bytes=len(compressed_data),
            )

            # Store the datapoint reusing the same secure pipeline
            with self.operation_duration.labels(operation='store_datapoint').time():
                await self._store_datapoint(datapoint, compressed_data)

            logger.info(
                "Collected advisor decision datapoint",
                extra={
                    "game_mode": game_mode,
                    "profession": profession,
                    "role": role,
                    "source": getattr(source, "value", str(source)),
                },
            )

            return datapoint

        except Exception as e:
            logger.error(f"Error collecting advisor decision: {e}")
            raise

    def _compress_data(self, data: Dict) -> bytes:
        """Compress data using zlib."""
        json_str = json.dumps(data, separators=(",", ":"))
        return zlib.compress(json_str.encode("utf-8"))

    def _validate_datapoint_id(self, datapoint_id: str) -> bool:
        """
        Validate that a datapoint ID is safe to use in file paths.
        
        Args:
            datapoint_id: ID to validate
            
        Returns:
            bool: True if the ID is valid, False otherwise
        """
        if not datapoint_id or not isinstance(datapoint_id, str):
            return False
        
        # Check if it's a valid UUID
        try:
            uuid.UUID(datapoint_id)
        except (ValueError, AttributeError):
            return False
        
        # Prevent directory traversal
        if ".." in datapoint_id or "/" in datapoint_id or "\\" in datapoint_id:
            return False
            
        return True

    def _sanitize_input(self, data: Any) -> Any:
        """
        Sanitize input data to prevent injection attacks.
        
        Args:
            data: Data to sanitize
            
        Returns:
            Sanitized data
        """
        if data is None:
            return None
            
        if isinstance(data, dict):
            return {k: self._sanitize_input(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_input(item) for item in data]
        elif isinstance(data, str):
            # More comprehensive XSS protection
            import html
            return html.escape(data)
        return data

    def _validate_data_size(self, data: Dict) -> bool:
        """
        Validate that the data size is within reasonable limits.
        
        Args:
            data: Data to validate
            
        Returns:
            bool: True if data size is acceptable, False otherwise
            
        Raises:
            ValueError: If data size exceeds the limit
        """
        # 10KB limit for raw JSON data (will be compressed later)
        # This is a low limit for testing purposes
        MAX_JSON_SIZE = 10 * 1024  # 10KB
        
        try:
            json_str = json.dumps(data)
            size = len(json_str.encode('utf-8'))
            
            if size > MAX_JSON_SIZE:
                logger.warning(f"Data size {size} exceeds maximum allowed size {MAX_JSON_SIZE}")
                return False
                
            return True
            
        except (TypeError, ValueError) as e:
            logger.error(f"Error validating data size: {e}")
            return False

    def _json_serializer(self, obj):
        """JSON serializer for objects not serializable by default json code."""
        if isinstance(obj, (datetime, datetime_type)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    def _decompress_data(self, compressed: bytes) -> Dict:
        """Decompress data with size validation."""
        # Limit decompressed size to 10MB
        MAX_DECOMPRESSED_SIZE = 10 * 1024 * 1024
        
        # Create a decompression object with size limit
        decompressor = zlib.decompressobj()
        try:
            # Decompress in chunks to prevent memory exhaustion
            chunks = []
            total_size = 0
            
            while True:
                chunk = decompressor.decompress(compressed, 8192)  # 8KB chunks
                if not chunk:
                    break
                    
                chunks.append(chunk)
                total_size += len(chunk)
                
                if total_size > MAX_DECOMPRESSED_SIZE:
                    raise ValueError("Decompressed data exceeds size limit")
                    
            json_str = b''.join(chunks).decode('utf-8')
            return json.loads(json_str)
            
        except zlib.error as e:
            logger.error(f"Decompression error: {e}")
            raise ValueError("Invalid compressed data") from e

    def _track_operation_time(self, operation: str, duration: float):
        """Track operation time for performance monitoring."""
        self.operation_duration.labels(operation=operation).observe(duration)
        
        # Keep last 100 samples for each operation
        self._operation_times[operation].append(duration)
        if len(self._operation_times[operation]) > 100:
            self._operation_times[operation].pop(0)
    
    def get_operation_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all tracked operations."""
        stats = {}
        for op, times in self._operation_times.items():
            if times:
                stats[op] = {
                    'count': len(times),
                    'avg': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times),
                    'p95': sorted(times)[int(len(times) * 0.95)] if len(times) > 5 else None
                }
        return stats
    
    async def _store_datapoint(
        self,
        datapoint: TrainingDatapoint,
        compressed_data: bytes,
    ) -> None:
        """
        Store datapoint to disk and update cache with security validations.
        
        Args:
            datapoint: Datapoint to store
            compressed_data: Compressed data to store
            
        Raises:
            ValueError: If validation fails
            IOError: If there's an error writing to disk
        """
        start_time = time.time()
        datapoint_id = str(datapoint.id)
        
        try:
            # Validate datapoint ID
            if not self._validate_datapoint_id(datapoint_id):
                error_msg = f"Invalid datapoint ID: {datapoint_id}"
                self.collect_errors.labels(type='store', error='invalid_id').inc()
                raise ValueError(error_msg)
                
            # Validate data size
            if not self._validate_data_size(datapoint.data):
                error_msg = "Data size exceeds maximum allowed limit"
                self.collect_errors.labels(type='store', error='size_exceeded').inc()
                raise ValueError(error_msg)
                
            # Sanitize input data
            sanitized_data = self._sanitize_input(datapoint.data)
            datapoint.data = sanitized_data
            
            # Ensure directory exists with secure permissions
            try:
                self.storage_path.mkdir(parents=True, exist_ok=True, mode=0o750)  # rwxr-x---
                
                # Ensure storage path is a directory and not a symlink
                if not self.storage_path.is_dir() or self.storage_path.is_symlink():
                    error_msg = f"Invalid storage path: {self.storage_path}"
                    self.collect_errors.labels(type='store', error='invalid_path').inc()
                    raise IOError(error_msg)
                    
            except Exception as e:
                error_msg = f"Failed to create storage directory: {e}"
                self.collect_errors.labels(type='store', error='io_error').inc()
                logger.error(error_msg)
                raise IOError(error_msg) from e

            # Store compressed data with atomic write
            data_file = self.storage_path / f"{datapoint_id}.bin"
            temp_file = data_file.with_suffix(".tmp")
            
            try:
                # Write to temporary file first
                with open(temp_file, "wb") as f:
                    f.write(compressed_data)
                
                # Atomic rename
                if data_file.exists():
                    os.remove(data_file)
                os.rename(temp_file, data_file)
            except Exception as e:
                # Cleanup temp file on error
                if temp_file.exists():
                    os.remove(temp_file)
                raise

            # Prepare metadata (without the data field)
            metadata = datapoint.model_dump(mode="json", exclude={"data"})
            metadata_str = json.dumps(metadata) + "\n"
            
            # Update metadata file with atomic write
            metadata = datapoint.model_dump(exclude={"data"})
            temp_meta = self.datapoints_file.with_suffix(".tmp")
            
            try:
                # Read existing metadata
                existing_metadata = {}
                if self.datapoints_file.exists():
                    with open(self.datapoints_file, "r") as f:
                        for i, line in enumerate(f, 1):
                            try:
                                item = json.loads(line)
                                existing_metadata[item["id"]] = item
                            except json.JSONDecodeError as e:
                                logger.error(
                                    f"Error parsing metadata line {i} in {self.datapoints_file}: {e}",
                                    extra={
                                        'file': str(self.datapoints_file),
                                        'line_number': i,
                                        'line_content': line.strip()
                                    }
                                )
                                continue
                
                # Add/update the current datapoint
                existing_metadata[datapoint_id] = metadata
                
                # Write to temporary file with custom JSON serializer
                try:
                    with open(temp_meta, "w") as f:
                        for item in existing_metadata.values():
                            f.write(json.dumps(item, default=self._json_serializer) + "\n")
                except IOError as e:
                    error_msg = f"Failed to write metadata to {temp_meta}: {e}"
                    logger.error(error_msg)
                    raise IOError(error_msg) from e
                
                # Atomic replace of the original file
                os.replace(temp_meta, self.datapoints_file)
                
                # Update in-memory cache
                self._metadata_cache[datapoint_id] = metadata
                
                # Update metrics
                self.datapoints_count.inc()
                
            except Exception as e:
                error_type = type(e).__name__
                self.collect_errors.labels(type='store', error=f'metadata_{error_type}').inc()
                
                # Cleanup temp file on error
                if temp_meta.exists():
                    try:
                        os.remove(temp_meta)
                    except Exception as cleanup_error:
                        logger.error(
                            f"Failed to clean up temp metadata file {temp_meta}: {cleanup_error}",
                            exc_info=True
                        )
                
                logger.error(
                    f"Error updating metadata file: {e}",
                    extra={
                        'datapoint_id': datapoint_id,
                        'error_type': error_type,
                        'error': str(e)
                    },
                    exc_info=True
                )
                raise
                
            # Clear the cache for this datapoint
            if hasattr(self.load_datapoint, "cache_info"):
                self.load_datapoint.cache_clear()
            
            # Log successful storage
            duration = time.time() - start_time
            self._track_operation_time('store_datapoint', duration)
            
            logger.info(
                f"Stored datapoint {datapoint_id}",
                extra={
                    'datapoint_id': datapoint_id,
                    'build_id': getattr(datapoint, 'build_id', 'unknown'),
                    'source': getattr(datapoint, 'source', 'unknown'),
                    'compressed_size': len(compressed_data),
                    'storage_time_seconds': duration
                }
            )

        except Exception as e:
            error_type = type(e).__name__
            self.collect_errors.labels(type='store', error=error_type).inc()
            
            logger.error(
                f"Error storing datapoint {getattr(datapoint, 'id', 'unknown')}: {e}",
                extra={
                    'datapoint_id': getattr(datapoint, 'id', 'unknown'),
                    'error_type': error_type,
                    'error': str(e)
                },
                exc_info=True
            )
            raise

    async def load_datapoint(self, datapoint_id: str) -> Optional[TrainingDatapoint]:
        """Load a datapoint by ID with simple in-memory caching.

        The cache is implemented via the in-memory metadata cache:
        - First access: metadata is loaded (if needed) and data is read from disk.
          This is counted as a cache miss.
        - Subsequent accesses in the same process use the `data` field already
          stored in the metadata cache, counted as cache hits.
        """
        start_time = time.time()
        cache_hit = False
        success = False

        try:
            # Ensure metadata is loaded
            if not self._metadata_loaded:
                await self._load_metadata()

            # Check if datapoint exists in metadata
            if datapoint_id not in self._metadata_cache:
                self.cache_misses.labels(operation='load_datapoint').inc()
                logger.warning(
                    f"Datapoint not found: {datapoint_id}",
                    extra={'datapoint_id': datapoint_id},
                )
                return None

            # Get metadata from cache
            meta = self._metadata_cache[datapoint_id]

            # If data is already in memory, this is a cache hit
            if 'data' in meta and meta['data'] is not None:
                cache_hit = True
                self.cache_hits.labels(operation='load_datapoint').inc()

                datapoint = TrainingDatapoint(
                    id=datapoint_id,
                    build_id=meta['build_id'],
                    team_id=meta.get('team_id'),
                    data=meta['data'],
                    game_mode=meta.get('game_mode'),
                    profession=meta.get('profession'),
                    role=meta.get('role'),
                    source=meta.get('source', DataSource.AI_GENERATED),
                    compressed_size_bytes=meta.get('compressed_size_bytes', 0),
                    created_at=meta.get('created_at'),
                )

                logger.info(
                    f"Cache hit for datapoint {datapoint_id}",
                    extra={
                        'datapoint_id': datapoint_id,
                        'cache_hit': True,
                    },
                )
                success = True
                return datapoint

            # If we get here, we need to load the data from disk (cache miss)
            data_file = self.storage_path / f"{datapoint_id}.bin"
            if not data_file.exists():
                self.cache_misses.labels(operation='load_datapoint').inc()
                logger.error(
                    f"Data file not found for datapoint {datapoint_id}",
                    extra={'datapoint_id': datapoint_id, 'file_path': str(data_file)},
                )
                return None

            try:
                with open(data_file, 'rb') as f:
                    compressed_data = f.read()

                data = self._decompress_data(compressed_data)

                # Cache the data in metadata for future use
                meta['data'] = data

                datapoint = TrainingDatapoint(
                    id=datapoint_id,
                    build_id=meta['build_id'],
                    team_id=meta.get('team_id'),
                    data=data,
                    game_mode=meta.get('game_mode'),
                    profession=meta.get('profession'),
                    role=meta.get('role'),
                    source=meta.get('source', DataSource.AI_GENERATED),
                    compressed_size_bytes=meta.get('compressed_size_bytes', 0),
                    created_at=meta.get('created_at'),
                )

                self.cache_misses.labels(operation='load_datapoint').inc()
                success = True
                return datapoint

            except Exception as e:
                error_type = type(e).__name__
                self.collect_errors.labels(type='load', error=error_type).inc()
                logger.error(
                    f"Error loading datapoint {datapoint_id}",
                    extra={
                        'datapoint_id': datapoint_id,
                        'error_type': error_type,
                        'error_message': str(e),
                    },
                    exc_info=True,
                )
                return None

        finally:
            duration = time.time() - start_time
            # Track operation time in histogram and internal stats
            self.operation_duration.labels(operation='load_datapoint').observe(duration)
            self._track_operation_time('load_datapoint', duration)

            logger.debug(
                f"Loaded datapoint {datapoint_id}",
                extra={
                    'datapoint_id': datapoint_id,
                    'duration_seconds': duration,
                    'cache_hit': cache_hit,
                    'success': success,
                },
            )

    async def _load_metadata(self):
        """
        Load metadata from disk into memory.
        
        Raises:
            IOError: If there's an error reading the metadata file
            json.JSONDecodeError: If the metadata file contains invalid JSON
        """
        if self._metadata_loaded:
            return
            
        start_time = time.time()
        self._metadata_cache = {}
        
        try:
            if not self.datapoints_file.exists():
                self._metadata_loaded = True
                logger.debug("No metadata file found, starting with empty cache")
                return
                
            logger.debug(f"Loading metadata from {self.datapoints_file}")
            load_errors = 0
            
            with open(self.datapoints_file, 'r') as f:
                for i, line in enumerate(f, 1):
                    try:
                        item = json.loads(line)
                        if 'id' not in item:
                            logger.warning(
                                f"Missing 'id' in metadata line {i}",
                                extra={'line_number': i, 'line_content': line.strip()}
                            )
                            load_errors += 1
                            continue
                            
                        # Convert string dates back to datetime objects
                        if 'created_at' in item and isinstance(item['created_at'], str):
                            try:
                                item['created_at'] = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
                            except (ValueError, TypeError) as e:
                                logger.warning(
                                    f"Invalid date format in metadata for {item['id']}",
                                    extra={
                                        'datapoint_id': item['id'],
                                        'created_at': item['created_at'],
                                        'error': str(e)
                                    }
                                )
                                item['created_at'] = datetime.utcnow()
                        
                        self._metadata_cache[item['id']] = item
                        
                    except json.JSONDecodeError as e:
                        load_errors += 1
                        logger.error(
                            f"Error parsing JSON in metadata line {i}",
                            extra={
                                'line_number': i,
                                'line_content': line.strip(),
                                'error': str(e)
                            },
                            exc_info=True
                        )
                        continue
            
            self._metadata_loaded = True
            loaded_count = len(self._metadata_cache)
            
            duration = time.time() - start_time
            logger.info(
                f"Loaded {len(self._metadata_cache)} metadata entries" + 
                (f" with {load_errors} errors" if load_errors else ""),
                extra={
                    'metadata_entries': len(self._metadata_cache),
                    'load_errors': load_errors,
                    'load_time_seconds': duration
                }
            )
            
        except Exception as e:
            error_type = type(e).__name__
            self.collect_errors.labels(type='metadata', error=error_type).inc()
            
            logger.error(
                f"Error loading metadata from {self.datapoints_file}: {e}",
                extra={
                    'file': str(self.datapoints_file),
                    'error_type': error_type,
                    'error': str(e)
                },
                exc_info=True
            )
            
            self._metadata_cache = {}
            self._metadata_loaded = False
            raise

    async def get_all_datapoints(self) -> List[TrainingDatapoint]:
        """
        Load all datapoints (metadata only, without full data).
        
        Returns:
            List of datapoints with metadata only
        """
        if not self._metadata_loaded:
            await self._load_metadata()
        
        return [
            TrainingDatapoint(**metadata) 
            for metadata in self._metadata_cache.values()
        ]
