import { Router } from "express";

import {
  createAnalysisHandler,
  getAnalysesHandler,
  getAnalysisHandler,
} from "../controllers/analysis.controller.js";
import { handleAnalysisVideoUpload } from "../middleware/analysis-upload.middleware.js";

const analysisRouter = Router();

analysisRouter.post(
  "/",
  handleAnalysisVideoUpload,
  createAnalysisHandler,
);

analysisRouter.get("/", getAnalysesHandler);
analysisRouter.get("/:id", getAnalysisHandler);

export default analysisRouter;