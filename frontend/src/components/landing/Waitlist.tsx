import { CheckCircle2, Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { Reveal } from "@/components/landing/Reveal";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type FormValues = { email: string };

export function Waitlist() {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting, isSubmitSuccessful },
  } = useForm<FormValues>({ defaultValues: { email: "" } });

  const onSubmit = handleSubmit(async (values) => {
    await new Promise((r) => setTimeout(r, 700));
    toast.success("You're on the list", {
      description: `We'll email ${values.email} the moment early access opens.`,
    });
    reset({ email: "" });
  });

  return (
    <section id="waitlist" className="relative overflow-hidden py-24 sm:py-32">
      <div className="animated-gradient absolute inset-0 opacity-70" aria-hidden />
      <div className="relative mx-auto max-w-3xl px-4 text-center sm:px-6">
        <Reveal>
          <h2 className="text-3xl font-semibold leading-tight text-foreground sm:text-5xl">
            Join the Future of Women's Health.
          </h2>
        </Reveal>
        <Reveal delay={0.08}>
          <p className="mx-auto mt-5 max-w-xl text-base leading-relaxed text-muted-foreground sm:text-lg">
            Early access opens in waves. Members on the waitlist receive three months of premium and
            help shape what we build next.
          </p>
        </Reveal>
        <Reveal delay={0.16}>
          <form
            onSubmit={onSubmit}
            noValidate
            className="glass-panel mx-auto mt-10 flex max-w-xl flex-col gap-3 rounded-3xl p-3 sm:flex-row"
          >
            <label htmlFor="waitlist-email" className="sr-only">
              Email address
            </label>
            <Input
              id="waitlist-email"
              type="email"
              inputMode="email"
              placeholder="you@example.com"
              aria-invalid={Boolean(errors.email)}
              className="h-12 flex-1 rounded-2xl border-transparent bg-surface text-base placeholder:text-muted-foreground"
              {...register("email", {
                required: "Please enter your email address",
                pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: "Enter a valid email" },
              })}
            />
            <Button type="submit" variant="hero" size="xl" disabled={isSubmitting}>
              {isSubmitting ? <Loader2 className="animate-spin" /> : null}
              Join Waitlist
            </Button>
          </form>
        </Reveal>
        {errors.email ? (
          <p role="alert" className="mt-3 text-sm font-medium text-destructive">
            {errors.email.message}
          </p>
        ) : null}
        {isSubmitSuccessful && !errors.email ? (
          <p className="mt-3 inline-flex items-center gap-2 text-sm font-medium text-success-foreground">
            <CheckCircle2 className="size-4" /> Thanks—check your inbox for a confirmation.
          </p>
        ) : null}
        <p className="mt-6 text-xs text-muted-foreground">
          No spam, no data selling. Unsubscribe in one click.
        </p>
      </div>
    </section>
  );
}