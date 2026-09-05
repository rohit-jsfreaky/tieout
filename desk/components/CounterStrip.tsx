import { Counter } from "./Counter";

/** Four counters in a recessed track. Human touches is the one that has to fall:
 *  five exceptions, one approval, and the rest clear themselves. */
export function CounterStrip() {
  return (
    <div className="well flex gap-1 rounded-lg bg-soft p-1">
      <Counter label="Human touches" value={null} winning />
      <Counter label="Auto-cleared" value={null} />
      <Counter label="Refused" value={null} />
      <Counter label="Evidence items" value={null} />
    </div>
  );
}
