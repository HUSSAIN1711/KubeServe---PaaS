import { redirect } from 'next/navigation';
import { auth } from '@/lib/auth';

export default function Home() {
  // Redirect to dashboard if authenticated, otherwise to login
  if (auth.isAuthenticated()) {
    redirect('/dashboard');
  } else {
    redirect('/login');
  }
}

