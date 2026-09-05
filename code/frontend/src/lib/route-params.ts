export function requireRouteParam(value: string | undefined, name: string): string {
  if (!value) throw new Error(`Missing required route parameter: ${name}`);
  return value;
}
