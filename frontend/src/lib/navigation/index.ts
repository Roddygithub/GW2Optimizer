export function navigate(path: string) {
  if (typeof window !== 'undefined') {
    window.location.href = path;
  }
}
