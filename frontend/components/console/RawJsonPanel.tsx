'use client';

import { useState } from 'react';
import { Copy, ChevronDown, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { EnrichmentJob } from '@/src/lib/types';
import { copyToClipboard } from '@/src/lib/utils';

type RawJsonPanelProps = {
  job: EnrichmentJob;
};

export function RawJsonPanel({ job }: RawJsonPanelProps) {
  const [open, setOpen] = useState(false);

  const json = JSON.stringify(job, null, 2);

  return (
    <Collapsible open={open} onOpenChange={setOpen} className="rounded-lg border">
      <div className="flex items-center justify-between px-4 py-3">
        <CollapsibleTrigger asChild>
          <Button variant="ghost" size="sm" className="gap-2 px-0">
            {open ? <ChevronDown className="size-4" /> : <ChevronRight className="size-4" />}
            Raw JSON
          </Button>
        </CollapsibleTrigger>
        <Button variant="outline" size="sm" onClick={() => void copyToClipboard(json)}>
          <Copy className="mr-1 size-3" />
          Copy
        </Button>
      </div>
      <CollapsibleContent>
        <pre className="max-h-96 overflow-auto border-t bg-muted/30 p-4 text-xs">{json}</pre>
      </CollapsibleContent>
    </Collapsible>
  );
}
