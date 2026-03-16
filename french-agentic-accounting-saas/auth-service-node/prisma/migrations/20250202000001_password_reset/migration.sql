-- CreateTable
CREATE TABLE "auth_password_reset_tokens" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "user_id" UUID NOT NULL,
    "token_hash" TEXT NOT NULL,
    "expires_at" TIMESTAMP(3) NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "auth_password_reset_tokens_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "auth_password_reset_tokens_token_hash_key" ON "auth_password_reset_tokens"("token_hash");

-- CreateIndex
CREATE INDEX "auth_password_reset_tokens_user_id_idx" ON "auth_password_reset_tokens"("user_id");

-- CreateIndex
CREATE INDEX "auth_password_reset_tokens_token_hash_idx" ON "auth_password_reset_tokens"("token_hash");

-- CreateIndex
CREATE INDEX "auth_password_reset_tokens_expires_at_idx" ON "auth_password_reset_tokens"("expires_at");

-- AddForeignKey
ALTER TABLE "auth_password_reset_tokens" ADD CONSTRAINT "auth_password_reset_tokens_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth_users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
