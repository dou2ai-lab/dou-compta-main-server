/**
 * Seed: default tenant + seed users (admin@example.com / password).
 * Run with: npx prisma db seed (or npm run db:seed)
 */
import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcrypt';

const prisma = new PrismaClient();
const SALT_ROUNDS = 12;

async function main() {
  const tenant = await prisma.tenant.upsert({
    where: { slug: 'default' },
    update: {},
    create: {
      name: 'Default Tenant',
      slug: 'default',
      status: 'active',
    },
  });
  console.log('Default tenant:', tenant.id);

  const seedPasswordHash = await bcrypt.hash('password', SALT_ROUNDS);
  const seedUsers = [
    { email: 'admin@example.com', firstName: 'Admin', lastName: 'User' },
    { email: 'approver@example.com', firstName: 'Approver', lastName: 'User' },
    { email: 'user@example.com', firstName: 'Test', lastName: 'User' },
  ];
  for (const u of seedUsers) {
    await prisma.user.upsert({
      where: { email: u.email },
      update: {},
      create: {
        email: u.email,
        firstName: u.firstName,
        lastName: u.lastName,
        passwordHash: seedPasswordHash,
        tenantId: tenant.id,
        status: 'active',
      },
    });
    console.log('Seed user:', u.email);
  }
  console.log('Seed users can log in with password: password');
}

main()
  .then(() => prisma.$disconnect())
  .catch((e) => {
    console.error(e);
    prisma.$disconnect();
    process.exit(1);
  });
