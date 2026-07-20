import { Router } from "express";

import {
  createAnalysisHandler,
  getAnalysesHandler,
  getAnalysisHandler,
} from "../controllers/analysis.controller.js";

const analysisRouter = Router();

analysisRouter.post("/", createAnalysisHandler);
analysisRouter.get("/", getAnalysesHandler);
analysisRouter.get("/:id", getAnalysisHandler);

export default analysisRouter;