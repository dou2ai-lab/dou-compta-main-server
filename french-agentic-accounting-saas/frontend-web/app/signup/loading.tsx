'use client';

export default function SignupLoading() {
  return (
    <div className="flex h-screen items-center justify-center bg-bgPage">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto" />
        <p className="mt-4 text-textSecondary">Chargement...</p>
      </div>
    </div>
  );
}
