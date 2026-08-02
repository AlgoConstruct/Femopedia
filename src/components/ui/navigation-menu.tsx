import * as React from "react";
import * as NavigationMenuPrimitive from "@radix-ui/react-navigation-menu";
import { cva } from "class-variance-authority";
import { ChevronDownIcon } from "lucide-react";
import { cn } from "@/lib/utils";

function NavigationMenu({ className, children, viewport = true, ...props }: React.ComponentProps<typeof NavigationMenuPrimitive.Root> & { viewport?: boolean }) {
  return <NavigationMenuPrimitive.Root data-slot="navigation-menu" data-viewport={viewport} className={cn("group/navigation-menu relative flex max-w-max flex-1 items-center justify-center", className)} {...props}>{children}{viewport && <NavigationMenuViewport />}</NavigationMenuPrimitive.Root>;
}
function NavigationMenuList({ className, ...props }: React.ComponentProps<typeof NavigationMenuPrimitive.List>) {
  return <NavigationMenuPrimitive.List data-slot="navigation-menu-list" className={cn("group flex flex-1 list-none items-center justify-center gap-1", className)} {...props} />;
}
function NavigationMenuItem({ className, ...props }: React.ComponentProps<typeof NavigationMenuPrimitive.Item>) {
  return <NavigationMenuPrimitive.Item data-slot="navigation-menu-item" className={cn("relative", className)} {...props} />;
}
const navigationMenuTriggerStyle = cva("group inline-flex h-9 w-max cursor-pointer items-center justify-center rounded-full bg-transparent px-3 py-2 text-sm font-semibold text-muted-foreground transition-[color,background-color,box-shadow] hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-ring/10 disabled:pointer-events-none disabled:opacity-50 data-[active=true]:bg-accent/50 data-[state=open]:bg-accent/50 data-[state=open]:text-accent-foreground");
function NavigationMenuTrigger({ className, children, ...props }: React.ComponentProps<typeof NavigationMenuPrimitive.Trigger>) {
  return <NavigationMenuPrimitive.Trigger data-slot="navigation-menu-trigger" className={cn(navigationMenuTriggerStyle(), className)} {...props}>{children}<ChevronDownIcon className="relative top-px ms-1 size-3.5 opacity-60 transition duration-300 group-data-[state=open]:rotate-180" aria-hidden="true" /></NavigationMenuPrimitive.Trigger>;
}
function NavigationMenuContent({ className, ...props }: React.ComponentProps<typeof NavigationMenuPrimitive.Content>) {
  return <NavigationMenuPrimitive.Content data-slot="navigation-menu-content" className={cn("top-0 left-0 w-full p-2 md:absolute md:w-auto data-[motion^=from-]:animate-in data-[motion^=to-]:animate-out data-[motion^=from-]:fade-in data-[motion^=to-]:fade-out data-[motion=from-end]:slide-in-from-right-52 data-[motion=from-start]:slide-in-from-left-52 data-[motion=to-end]:slide-out-to-right-52 data-[motion=to-start]:slide-out-to-left-52 group-data-[viewport=false]/navigation-menu:top-full group-data-[viewport=false]/navigation-menu:mt-1.5 group-data-[viewport=false]/navigation-menu:overflow-hidden group-data-[viewport=false]/navigation-menu:rounded-2xl group-data-[viewport=false]/navigation-menu:border group-data-[viewport=false]/navigation-menu:bg-popover group-data-[viewport=false]/navigation-menu:text-popover-foreground group-data-[viewport=false]/navigation-menu:shadow-xl", className)} {...props} />;
}
function NavigationMenuViewport({ className, ...props }: React.ComponentProps<typeof NavigationMenuPrimitive.Viewport>) {
  return <div className="absolute top-full left-1/2 isolate z-50 flex -translate-x-1/2 justify-center"><NavigationMenuPrimitive.Viewport data-slot="navigation-menu-viewport" className={cn("relative mt-2 h-[var(--radix-navigation-menu-viewport-height)] w-full origin-top-center overflow-hidden rounded-2xl border border-border bg-popover p-1.5 text-popover-foreground shadow-xl shadow-black/5 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-90 md:w-[var(--radix-navigation-menu-viewport-width)]", className)} {...props} /></div>;
}
function NavigationMenuLink({ className, ...props }: React.ComponentProps<typeof NavigationMenuPrimitive.Link>) {
  return <NavigationMenuPrimitive.Link data-slot="navigation-menu-link" className={cn("flex flex-col gap-1 rounded-xl p-3 text-sm transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-ring/10", className)} {...props} />;
}
function NavigationMenuIndicator({ className, ...props }: React.ComponentProps<typeof NavigationMenuPrimitive.Indicator>) {
  return <NavigationMenuPrimitive.Indicator data-slot="navigation-menu-indicator" className={cn("top-full z-[1] flex h-1.5 items-end justify-center overflow-hidden data-[state=visible]:animate-in data-[state=hidden]:animate-out data-[state=hidden]:fade-out data-[state=visible]:fade-in", className)} {...props}><div className="relative top-[60%] h-2 w-2 rotate-45 rounded-tl-sm bg-border shadow-md" /></NavigationMenuPrimitive.Indicator>;
}
export { NavigationMenu, NavigationMenuList, NavigationMenuItem, NavigationMenuContent, NavigationMenuTrigger, NavigationMenuLink, NavigationMenuIndicator, NavigationMenuViewport, navigationMenuTriggerStyle };
