import FeaturesSection from '../../components/landing/features-section';
import FooterSection from '../../components/landing/footer-section';
import ForTeamsSection from '../../components/landing/for-teams-section';
import HeroSection from '../../components/landing/hero-section';
import HowItWorksSection from '../../components/landing/how-it-works-section';
import LandingNavbar from '../../components/landing/landing-navbar';
import OpenSourceSection from '../../components/landing/open-source-section';
import RemoteWorkersSection from '../../components/landing/remote-workers-section';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <LandingNavbar />
      <main>
        <HeroSection />
        <FeaturesSection />
        <HowItWorksSection />
        <ForTeamsSection />
        <RemoteWorkersSection />
        <OpenSourceSection />
      </main>
      <FooterSection />
    </div>
  );
}
