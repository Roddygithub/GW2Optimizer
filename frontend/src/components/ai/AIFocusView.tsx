import { motion } from 'framer-motion';
import { X, AlertTriangle, Loader2 } from 'lucide-react';
import { Card, CardHeader, CardBody, CardFooter } from '../ui/CardPremium';
import { Button } from '../ui/ButtonPremium';

interface AIFocusViewProps {
  isLoading: boolean;
  data?: {
    synergy_score: number;
    suggestions: string[];
    missing_boons: string[];
    composition?: {
      builds: Array<{
        profession: string;
        role: string;
        count: number;
      }>;
    };
  };
  error?: Error | null;
  onClose: () => void;
}

export const AIFocusView = ({
  isLoading,
  data,
  error,
  onClose,
}: AIFocusViewProps) => (
  <motion.div
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
    className="fixed inset-0 bg-gw-dark/90 backdrop-blur-md z-50 flex items-center justify-center p-4"
    onClick={onClose}
  >
    <motion.div
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{
        delay: 0.1,
        type: 'spring',
        stiffness: 300,
        damping: 25,
      }}
      className="relative w-full max-w-2xl"
      onClick={(e) => e.stopPropagation()}
    >
      <Card className="max-h-[80vh] flex flex-col">
        <CardHeader title="Analyse IA Mistral (Mode Focus)">
          <Button variant="ghost" onClick={onClose} className="!p-1">
            <X className="h-5 w-5" />
          </Button>
        </CardHeader>

        <CardBody className="flex-grow overflow-y-auto space-y-4">
          {isLoading && (
            <div className="flex flex-col items-center justify-center h-48">
              <Loader2 className="h-12 w-12 text-gw-red animate-spin" />
              <p className="mt-4 text-gw-gray font-serif">
                Mistral analyse les permutations...
              </p>
            </div>
          )}

          {error && (
            <div className="flex flex-col items-center justify-center h-48">
              <AlertTriangle className="h-12 w-12 text-gw-red" />
              <p className="mt-4 text-gw-offwhite font-serif">
                Erreur de l'IA
              </p>
              <p className="mt-2 text-gw-gray">{error.message}</p>
            </div>
          )}

          {data && (
            <div className="space-y-4">
              {/* Score de Synergie */}
              <div>
                <h4 className="font-serif text-gw-gold mb-2">
                  Score de Synergie: {data.synergy_score}/10
                </h4>
                <div className="w-full bg-gw-dark rounded-full h-2.5">
                  <motion.div
                    className="bg-gw-gold h-2.5 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${data.synergy_score * 10}%` }}
                    transition={{ duration: 1, delay: 0.5 }}
                  />
                </div>
              </div>

              {/* Composition */}
              {data.composition && (
                <div>
                  <h4 className="font-serif text-gw-gold mb-2">
                    Composition Générée
                  </h4>
                  <div className="grid grid-cols-2 gap-2">
                    {data.composition.builds.map((build, i) => (
                      <div
                        key={i}
                        className="bg-gw-dark p-2 rounded-md border border-gw-gold/20"
                      >
                        <p className="text-sm font-medium text-gw-offwhite">
                          {build.count}x {build.profession}
                        </p>
                        <p className="text-xs text-gw-gray">{build.role}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Suggestions */}
              <div>
                <h4 className="font-serif text-gw-gold mb-2">
                  Suggestions d'optimisation
                </h4>
                <ul className="list-disc list-inside space-y-2 text-gw-offwhite">
                  {data.suggestions.map((s, i) => (
                    <li key={i} className="text-sm">
                      {s}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Auras Manquantes */}
              <div>
                <h4 className="font-serif text-gw-gold mb-2">
                  Auras Manquantes
                </h4>
                {data.missing_boons.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {data.missing_boons.map((b) => (
                      <span
                        key={b}
                        className="px-3 py-1 bg-gw-red/20 text-gw-red border border-gw-red/50 rounded-full text-sm"
                      >
                        {b}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-gw-gray italic text-sm">
                    Aucune aura majeure manquante.
                  </p>
                )}
              </div>
            </div>
          )}
        </CardBody>

        <CardFooter>
          <Button onClick={onClose} variant="secondary" className="w-full">
            Fermer
          </Button>
        </CardFooter>
      </Card>
    </motion.div>
  </motion.div>
);
