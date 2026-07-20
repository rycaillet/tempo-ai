-- AlterTable
ALTER TABLE "Analysis" ADD COLUMN     "backswingSeconds" DOUBLE PRECISION,
ADD COLUMN     "consistencyScore" INTEGER,
ADD COLUMN     "downswingSeconds" DOUBLE PRECISION,
ADD COLUMN     "primaryFinding" TEXT,
ADD COLUMN     "recommendation" TEXT,
ADD COLUMN     "swingScore" INTEGER,
ADD COLUMN     "tempoRatio" DOUBLE PRECISION;
