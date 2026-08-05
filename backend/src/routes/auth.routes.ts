import { Router } from "express";
import { rateLimit } from "express-rate-limit";

import {
  getCurrentUserHandler,
  loginHandler,
  logoutHandler,
  registerHandler,
} from "../controllers/auth.controller.js";
import { requireAuth } from "../middleware/require-auth.middleware.js";

const authRouter = Router();

const loginRateLimit = rateLimit({
  windowMs: 15 * 60 * 1000,
  limit: 10,
  standardHeaders: "draft-8",
  legacyHeaders: false,

  message: {
    message:
      "Too many login attempts. Try again later.",
  },
});

const registrationRateLimit = rateLimit({
  windowMs: 60 * 60 * 1000,
  limit: 5,
  standardHeaders: "draft-8",
  legacyHeaders: false,

  message: {
    message:
      "Too many account creation attempts. Try again later.",
  },
});

authRouter.post(
  "/register",
  registrationRateLimit,
  registerHandler,
);

authRouter.post(
  "/login",
  loginRateLimit,
  loginHandler,
);

authRouter.get(
  "/me",
  requireAuth,
  getCurrentUserHandler,
);

authRouter.post(
  "/logout",
  logoutHandler,
);

export default authRouter;