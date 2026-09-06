import {
  NumberCircleFour,
  NumberCircleOne,
  NumberCircleThree,
  NumberCircleTwo,
  type Icon,
} from "@phosphor-icons/react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const STEPS: { mark: Icon; title: string; line: string }[] = [
  {
    mark: NumberCircleOne,
    title: "One exception is investigated",
    line: "The ERP, the mailbox and the supplier portal. Every fact is filed with its source, its time and, on the portal, a screenshot.",
  },
  {
    mark: NumberCircleTwo,
    title: "One person decides",
    line: "Their name and their seat are recorded with the decision. Nothing is ever learned from a decision nobody signed.",
  },
  {
    mark: NumberCircleThree,
    title: "The rule is drafted, then clamped",
    line: "The model writes the wording; code writes the condition and inherits the approver's ceiling. A rule can never clear more than the person who taught it could have cleared by hand.",
  },
  {
    mark: NumberCircleFour,
    title: "The next one of that kind clears itself",
    line: "Citing the rule and that person. It shows up above as a citation, and on the audit trail as a decision nobody had to make.",
  },
];

/**
 * Where a rule on this page came from.
 *
 * The four steps are `engine/policy.py` in English, in the order that file runs
 * them — not a marketing diagram. A reader who wants the real thing can open the
 * rule above and read the condition code actually evaluates.
 */
export function PolicyLoopCard() {
  return (
    <Card className="bg-soft">
      <CardHeader>
        <CardTitle>How a rule is born</CardTitle>
        <CardDescription>
          Every line in the table above came through these four steps, in this
          order, exactly once.
        </CardDescription>
      </CardHeader>

      <CardContent>
        <ol className="flex flex-col gap-3">
          {STEPS.map((step) => {
            const Mark = step.mark;
            return (
              <li key={step.title} className="flex gap-2.5">
                <Mark
                  size={18}
                  weight="fill"
                  className="text-ledger mt-px shrink-0"
                  aria-hidden
                />
                <div className="min-w-0">
                  <p className="text-[13px] font-medium">{step.title}</p>
                  <p className="text-muted-foreground mt-0.5 text-xs leading-relaxed">
                    {step.line}
                  </p>
                </div>
              </li>
            );
          })}
        </ol>
      </CardContent>
    </Card>
  );
}
