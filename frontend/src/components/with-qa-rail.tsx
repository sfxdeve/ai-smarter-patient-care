import { useState } from "react"
import { MessageSquareText } from "lucide-react"

import { QaRail } from "@/components/qa-rail"
import { Button } from "@/components/ui/button"
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { useMediaQuery } from "@/hooks/use-media-query"

export function WithQaRail({
  children,
  subjectId,
  hadmId,
}: {
  children: React.ReactNode
  subjectId: number
  hadmId?: number | null
}) {
  const isDesktop = useMediaQuery("(min-width: 1024px)", true)
  const [sheetOpen, setSheetOpen] = useState(false)

  if (isDesktop) {
    return (
      <ResizablePanelGroup
        orientation="horizontal"
        className="h-auto! min-h-0 w-full!"
      >
        <ResizablePanel
          id="main"
          defaultSize="64"
          minSize="42"
          className="min-w-0"
        >
          <div className="pr-3">{children}</div>
        </ResizablePanel>
        <ResizableHandle withHandle className="mx-1" />
        <ResizablePanel
          id="qa"
          defaultSize="36"
          minSize="26"
          className="min-w-0"
        >
          <div className="sticky top-4 max-h-[calc(100svh-7rem)] overflow-y-auto pl-1">
            <QaRail subjectId={subjectId} hadmId={hadmId} />
          </div>
        </ResizablePanel>
      </ResizablePanelGroup>
    )
  }

  return (
    <>
      {children}
      <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
        <SheetTrigger
          render={
            <Button
              size="lg"
              className="fixed right-4 bottom-4 z-40 shadow-lg"
            />
          }
        >
          <MessageSquareText data-icon="inline-start" />
          Ask the record
        </SheetTrigger>
        <SheetContent
          side="right"
          className="w-full gap-0 p-0 sm:max-w-md"
          showCloseButton
        >
          <SheetHeader className="border-b">
            <SheetTitle>Ask the record</SheetTitle>
            <SheetDescription>
              {hadmId != null
                ? `Admission-scoped QA for admission ${hadmId}.`
                : "Patient-scoped QA (no Admission selected)."}
            </SheetDescription>
          </SheetHeader>
          <div className="min-h-0 flex-1 overflow-y-auto p-4">
            <QaRail
              subjectId={subjectId}
              hadmId={hadmId}
              className="border-0 p-0 shadow-none"
            />
          </div>
        </SheetContent>
      </Sheet>
    </>
  )
}
