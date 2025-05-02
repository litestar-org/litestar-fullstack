import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Link } from "@tanstack/react-router";

export function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted">
      <div className="container mx-auto px-4 py-16">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-primary to-primary/60">Welcome to Litestar App</h1>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            A powerful platform for team collaboration and project management. Join thousands of teams who are already using our platform to achieve their goals.
          </p>
          <div className="flex gap-4 justify-center">
            <Button asChild size="lg">
              <Link to="/login">Get Started</Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link to="/signup">Sign Up</Link>
            </Button>
          </div>
        </div>

        {/* Features Section */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <Card className="p-6">
            <div className="text-2xl mb-4">🚀</div>
            <h3 className="text-xl font-semibold mb-2">Fast & Efficient</h3>
            <p className="text-muted-foreground">Built with performance in mind, ensuring smooth and responsive experience.</p>
          </Card>
          <Card className="p-6">
            <div className="text-2xl mb-4">🔒</div>
            <h3 className="text-xl font-semibold mb-2">Secure & Reliable</h3>
            <p className="text-muted-foreground">Enterprise-grade security to keep your data safe and protected.</p>
          </Card>
          <Card className="p-6">
            <div className="text-2xl mb-4">🤝</div>
            <h3 className="text-xl font-semibold mb-2">Team Collaboration</h3>
            <p className="text-muted-foreground">Seamless collaboration tools to keep your team in sync.</p>
          </Card>
        </div>

        {/* CTA Section */}
        <div className="text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to Get Started?</h2>
          <p className="text-muted-foreground mb-8">Join our community of successful teams today.</p>
          <div className="flex gap-4 justify-center">
            <Button asChild size="lg" variant="outline">
              <Link to="/login">Login</Link>
            </Button>
            <Button asChild size="lg">
              <Link to="/signup">Sign Up</Link>
            </Button>
          </div>
        </div>

        {/* Footer Links */}
        <div className="mt-16 pt-8 border-t border-border">
          <div className="flex justify-center gap-8">
            <Link to="/privacy" className="text-sm text-muted-foreground hover:text-foreground">
              Privacy Policy
            </Link>
            <Link to="/terms" className="text-sm text-muted-foreground hover:text-foreground">
              Terms of Service
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
