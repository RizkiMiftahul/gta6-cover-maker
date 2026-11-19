// Panel zero is the main panel in every layout. Explicit assignments may repeat;
// automatic assignments consume each bundled scene at most once.
export const SAMPLE_NAMES = ['pier', 'boulevard', 'neon', 'coast', 'motel'];

export function panelSamples(count, primary = 'pier', explicit = []) {
  if (!SAMPLE_NAMES.includes(primary)) primary = 'pier';
  const assigned = Array.from({length: count}, (_, i) =>
    SAMPLE_NAMES.includes(explicit[i]) ? explicit[i] : null);
  if (!assigned[0]) assigned[0] = assigned.includes(primary)
    ? SAMPLE_NAMES.find(name => !assigned.includes(name)) || null : primary;
  const remaining = SAMPLE_NAMES.filter(name => !assigned.includes(name));
  return assigned.map(name => name || remaining.shift() || null);
}
