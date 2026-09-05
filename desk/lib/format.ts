/**
 * Turning the engine's vocabulary into English, and its numbers into figures.
 *
 * Presentation only. Nothing here decides anything, and nothing here computes a
 * quantity the API did not already send.
 */

import type {
  DecisionAction,
  ExceptionKind,
  ExceptionStatus,
  FactKind,
  Source,
} from "./api-types";

export function money(amount: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(amount);
}

/** Times on this screen are wall-clock: the reader is watching it happen. */
export function clock(iso: string): string {
  return new Date(iso).toLocaleTimeString("en-GB", { hour12: false });
}

export function day(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

const EXCEPTION_KIND: Record<ExceptionKind, string> = {
  short_ship: "Short ship",
  price_variance: "Price variance",
  missing_po: "No purchase order",
  unknown: "Unclassified",
};

const STATUS: Record<ExceptionStatus, string> = {
  open: "Open",
  proposed: "Awaiting a person",
  refused: "Refused",
  auto_cleared: "Auto-cleared",
  resolved: "Resolved",
};

const ACTION: Record<DecisionAction, string> = {
  short_pay: "Short-pay",
  approve: "Approve",
  attach_po: "Attach PO",
  reject: "Reject",
  refuse: "Refuse",
};

const FACT_KIND: Record<FactKind, string> = {
  invoice: "Invoice",
  purchase_order: "Purchase order",
  goods_receipt: "Goods receipt",
  candidate_purchase_order: "Candidate order",
  vendor_email: "Vendor email",
  delivery_note: "Delivery note",
  portal_absence: "Nothing on the portal",
};

const SOURCE: Record<Source, string> = {
  erp: "ERP",
  inbox: "Inbox",
  portal: "Portal",
};

export const exceptionKindLabel = (kind: ExceptionKind) => EXCEPTION_KIND[kind];
export const statusLabel = (status: ExceptionStatus) => STATUS[status];
export const actionLabel = (action: DecisionAction) => ACTION[action];
export const factKindLabel = (kind: FactKind) => FACT_KIND[kind];
export const sourceLabel = (source: Source) => SOURCE[source];

/** A Fact says who read it: `"code"`, or the id of the model that did. */
export function readerLabel(extractedBy: string): string {
  return extractedBy === "code" ? "read by code" : `read by ${extractedBy}`;
}
