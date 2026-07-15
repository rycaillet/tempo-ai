import { Router } from "express";

const healthRouter = Router();

healthRouter.get("/", (_request, response) => {
  response.status(200).json({
    status: "ok",
    service: "tempo-ai-api",
    timestamp: new Date().toISOString(),
  });
});

export default healthRouter;