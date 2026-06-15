import {
  LayoutDashboard,
  ShieldAlert,
  Search,
  FileText,
  Cpu,
  Settings,
  Building2,
  BookOpen,
  Target,
  ThumbsUp,
  CalendarDays,
  ScrollText,
  type LucideIcon,
} from 'lucide-react';

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  group: string;
}

export const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, group: 'Overview' },
  { label: 'Daily Summary', href: '/daily-summary', icon: CalendarDays, group: 'Overview' },

  { label: 'Alerts', href: '/alerts', icon: ShieldAlert, group: 'Operations' },
  { label: 'Investigations', href: '/investigations', icon: Search, group: 'Operations' },
  { label: 'Reports', href: '/reports', icon: FileText, group: 'Operations' },
  { label: 'Feedback', href: '/feedback', icon: ThumbsUp, group: 'Operations' },

  { label: 'AI Operations', href: '/ai-operations', icon: Cpu, group: 'Intelligence' },
  { label: 'MITRE ATT&CK', href: '/mitre', icon: Target, group: 'Intelligence' },
  { label: 'Playbooks', href: '/playbooks', icon: BookOpen, group: 'Intelligence' },

  { label: 'Customers', href: '/customers', icon: Building2, group: 'Administration' },
  { label: 'Settings', href: '/settings', icon: Settings, group: 'Administration' },
  { label: 'Audit Log', href: '/audit', icon: ScrollText, group: 'Administration' },
];

export const NAV_GROUPS = ['Overview', 'Operations', 'Intelligence', 'Administration'];
