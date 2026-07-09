import { MarketingShell } from '@/components/layout/MarketingShell';
import { OptOutForm } from '@/components/opt-out/OptOutForm';

export default function OptOutPage() {
  return (
    <MarketingShell>
      <div className="mx-auto max-w-xl px-4 py-12">
        <OptOutForm />
      </div>
    </MarketingShell>
  );
}
