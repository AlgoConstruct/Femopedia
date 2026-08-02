import { useState, type FormEvent } from "react";
import { ArrowRight, Check } from "lucide-react";

export function WaitlistSection() {
  const [email, setEmail] = useState("");
  const [joined, setJoined] = useState(false);
  function joinWaitlist(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (email) setJoined(true);
  }
  return (
    <section className="join-section" id="early-access" aria-labelledby="early-access-title">
      <div className="shell join-grid">
        <div>
          <p className="section-kicker light">Be here from the beginning</p>
          <h2 id="early-access-title">
            A healthier relationship
            <br />
            with health starts here.
          </h2>
          <p>Join the early community helping shape a more thoughtful future for women’s health.</p>
        </div>
        <form onSubmit={joinWaitlist} className="join-form">
          {joined ? (
            <div className="success-message" role="status">
              <Check /> You’re on the list. Welcome to Femopedia.
            </div>
          ) : (
            <>
              <label htmlFor="email">Email address</label>
              <div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@example.com"
                />
                <button type="submit">
                  Join early access <ArrowRight />
                </button>
              </div>
              <small>No spam. No data selling. Just meaningful updates.</small>
            </>
          )}
        </form>
      </div>
    </section>
  );
}
