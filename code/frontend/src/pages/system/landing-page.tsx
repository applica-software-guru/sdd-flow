import { Navigate } from 'react-router-dom';
import { useCurrentUser } from '../../hooks/use-auth';
import LandingNavbar from '../../components/landing/landing-navbar';
import HeroSection from '../../components/landing/hero-section';
import FeaturesSection from '../../components/landing/features-section';
import HowItWorksSection from '../../components/landing/how-it-works-section';
import ForTeamsSection from '../../components/landing/for-teams-section';
import RemoteWorkersSection from '../../components/landing/remote-workers-section';
import OpenSourceSection from '../../components/landing/open-source-section';
import FooterSection from '../../components/landing/footer-section';

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
      <RemoteWorkersSection />
      <OpenSourceSection />
      <FooterSection />
    </div>
  );
}
