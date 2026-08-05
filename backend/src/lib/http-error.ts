export class HttpError extends Error {
  readonly statusCode: number;
  readonly details?: unknown;

  constructor(
    statusCode: number,
    message: string,
    details?: unknown,
  ) {
    super(message);

    this.name = "HttpError";
    this.statusCode = statusCode;
    this.details = details;
  }
}