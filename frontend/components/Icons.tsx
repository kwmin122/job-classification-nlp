"use client";
/* Shared inline icons — stroke-based, 24x24, currentColor */
import React from "react";

type IconProps = { size?: number; sw?: number; [key: string]: unknown };
const mk = (paths: React.ReactNode) =>
  function Icon({ size = 20, sw = 1.8, ...rest }: IconProps) {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
        stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" {...rest}>
        {paths}
      </svg>
    );
  };

export const Target = mk(<><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.4" fill="currentColor" stroke="none"/></>);
export const Grid = mk(<><rect x="3.5" y="3.5" width="7" height="7" rx="1.5"/><rect x="13.5" y="3.5" width="7" height="7" rx="1.5"/><rect x="3.5" y="13.5" width="7" height="7" rx="1.5"/><rect x="13.5" y="13.5" width="7" height="7" rx="1.5"/></>);
export const Doc = mk(<><path d="M7 3.5h7l4 4V20a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4.5a1 1 0 0 1 1-1Z"/><path d="M14 3.5V8h4"/><path d="M9 13h6M9 16.5h4"/></>);
export const Layers = mk(<><path d="m12 3 8 4.5-8 4.5-8-4.5L12 3Z"/><path d="m4 12 8 4.5L20 12"/><path d="m4 16.5 8 4.5 8-4.5"/></>);
export const Book = mk(<><path d="M4 5.5A1.5 1.5 0 0 1 5.5 4H18a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1H6.5A2.5 2.5 0 0 0 4 21.5V5.5Z"/><path d="M4 18.5A2.5 2.5 0 0 1 6.5 16H19"/></>);
export const Map = mk(<><path d="m9 4-5 2v14l5-2 6 2 5-2V4l-5 2-6-2Z"/><path d="M9 4v14M15 6v14"/></>);
export const Settings = mk(<><circle cx="12" cy="12" r="3"/><path d="M12 2.5v2.5M12 19v2.5M21.5 12H19M5 12H2.5M18.7 5.3l-1.8 1.8M7.1 16.9l-1.8 1.8M18.7 18.7l-1.8-1.8M7.1 7.1 5.3 5.3"/></>);
export const Search = mk(<><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></>);
export const Bell = mk(<><path d="M6 9a6 6 0 0 1 12 0c0 5 1.5 6 1.5 6h-15S6 14 6 9Z"/><path d="M10 19a2 2 0 0 0 4 0"/></>);
export const Link = mk(<><path d="M10 13a3.5 3.5 0 0 0 5 0l3-3a3.5 3.5 0 0 0-5-5l-1.5 1.5"/><path d="M14 11a3.5 3.5 0 0 0-5 0l-3 3a3.5 3.5 0 0 0 5 5l1.5-1.5"/></>);
export const Upload = mk(<><path d="M12 16V4M8 8l4-4 4 4"/><path d="M5 16v3a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-3"/></>);
export const File = mk(<><path d="M7 3.5h7l4 4V20a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4.5a1 1 0 0 1 1-1Z"/><path d="M14 3.5V8h4"/></>);
export const Trash = mk(<><path d="M5 7h14M10 7V5.5a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1V7M6.5 7l.8 12a1 1 0 0 0 1 1h7.4a1 1 0 0 0 1-1l.8-12"/></>);
export const Plus = mk(<><path d="M12 5v14M5 12h14"/></>);
export const Refresh = mk(<><path d="M20 11a8 8 0 0 0-14-4M4 13a8 8 0 0 0 14 4"/><path d="M4 4v3.5h3.5M20 20v-3.5h-3.5"/></>);
export const Spark = mk(<><path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M18.4 5.6l-2.8 2.8M8.4 15.6l-2.8 2.8"/></>);
export const Check = mk(<><path d="M4.5 12.5 9.5 17.5 19.5 6.5"/></>);
export const CheckCircle = mk(<><circle cx="12" cy="12" r="9"/><path d="M8 12.2l2.8 2.8L16.5 9.3"/></>);
export const Alert = mk(<><path d="M12 8v5M12 16.5v.5"/><path d="M10.3 3.9 2.7 17.5A1.5 1.5 0 0 0 4 20h16a1.5 1.5 0 0 0 1.3-2.5L13.7 3.9a2 2 0 0 0-3.4 0Z"/></>);
export const Info = mk(<><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8v.5"/></>);
export const X = mk(<><path d="M6 6l12 12M18 6 6 18"/></>);
export const Chevron = mk(<><path d="m6 9 6 6 6-6"/></>);
export const ArrowRight = mk(<><path d="M5 12h14M13 6l6 6-6 6"/></>);
export const ArrowUpRight = mk(<><path d="M7 17 17 7M8 7h9v9"/></>);
export const Copy = mk(<><rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/></>);
export const Download = mk(<><path d="M12 4v11M8 11l4 4 4-4"/><path d="M5 20h14"/></>);
export const Pdf = mk(<><path d="M7 3.5h7l4 4V20a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4.5a1 1 0 0 1 1-1Z"/><path d="M14 3.5V8h4"/><path d="M8.5 16.5v-3h1a1 1 0 0 1 0 2h-1M12.5 13.5h1.5M12.5 13.5v3M16 13.5h1.6M16 15h1.2M16 13.5v3"/></>);
export const Clock = mk(<><circle cx="12" cy="12" r="9"/><path d="M12 7.5V12l3 2"/></>);
export const Bolt = mk(<><path d="M13 3 5 13h6l-1 8 8-10h-6l1-8Z"/></>);
export const User = mk(<><circle cx="12" cy="8" r="3.5"/><path d="M5.5 20a6.5 6.5 0 0 1 13 0"/></>);
export const Filter = mk(<><path d="M4 6h16M7 12h10M10 18h4"/></>);
export const Quote = mk(<><path d="M9 7H6a2 2 0 0 0-2 2v3a2 2 0 0 0 2 2h2v3H5M19 7h-3a2 2 0 0 0-2 2v3a2 2 0 0 0 2 2h2v3h-3"/></>);
export const Pin = mk(<><path d="M12 21s7-5.5 7-11a7 7 0 1 0-14 0c0 5.5 7 11 7 11Z"/><circle cx="12" cy="10" r="2.5"/></>);
export const Swap = mk(<><path d="M4 8h13M14 5l3 3-3 3M20 16H7M10 13l-3 3 3 3"/></>);
export const Eye = mk(<><path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z"/><circle cx="12" cy="12" r="3"/></>);
