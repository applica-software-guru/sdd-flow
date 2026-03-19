import { Navigate } from 'react-router-dom';
import { useCurrentUser } from '../../hooks/useAuth';
import LandingNavbar from '../../components/landing/LandingNavbar';
import HeroSection from '../../components/landing/HeroSection';
import FeaturesSection from '../../components/landing/FeaturesSection';
import HowItWorksSection from '../../components/landing/HowItWorksSection';
import ForTeamsSection from '../../components/landing/ForTeamsSection';
import OpenSourceSection from '../../components/landing/OpenSourceSection';
import FooterSection from '../../components/landing/FooterSection';

export default function LandingPage() {
  const { data: user, isLoading } = useCurrentUser();

  // Redirect authenticated users to dashboard
  if (!isLoading && user) {
    return <Navigate to="/tenants" replace />;
  }

  // Show landing page immediately — don't wait for auth check
  return (
    <div className="min-h-screen">
      <LandingNavbar />
      <HeroSection />
      <FeaturesSection />
      <HowItWorksSection />
      <ForTeamsSection />
      <OpenSourceSection />
      <FooterSection />
    </div>
  );
}
