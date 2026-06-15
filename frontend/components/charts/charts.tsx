'use client';

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { CHART_COLORS, severityColor, verdictColor } from '@/lib/utils';
import { EmptyState } from '@/components/ui/states';

const axisProps = {
  stroke: 'hsl(var(--muted-foreground))',
  fontSize: 11,
  tickLine: false,
  axisLine: false,
};

const tooltipStyle = {
  backgroundColor: 'hsl(var(--card))',
  border: '1px solid hsl(var(--border))',
  borderRadius: 8,
  fontSize: 12,
  color: 'hsl(var(--foreground))',
};

function NoData({ label }: { label?: string }) {
  return <EmptyState title={label || 'No data to display'} className="py-10" />;
}

export function AreaTrendChart({
  data,
  xKey,
  yKey,
  color = '#0ea5e9',
  height = 240,
  label,
}: {
  data?: any[];
  xKey: string;
  yKey: string;
  color?: string;
  height?: number;
  label?: string;
}) {
  if (!data || data.length === 0) return <NoData label={label} />;
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id={`grad-${yKey}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.4} />
            <stop offset="95%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
        <XAxis dataKey={xKey} {...axisProps} />
        <YAxis {...axisProps} allowDecimals={false} />
        <Tooltip contentStyle={tooltipStyle} cursor={{ stroke: 'hsl(var(--border))' }} />
        <Area
          type="monotone"
          dataKey={yKey}
          stroke={color}
          strokeWidth={2}
          fill={`url(#grad-${yKey})`}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function BarBreakdownChart({
  data,
  xKey,
  yKey,
  colorBy,
  color = '#8b5cf6',
  height = 240,
  label,
}: {
  data?: any[];
  xKey: string;
  yKey: string;
  colorBy?: 'severity' | 'verdict';
  color?: string;
  height?: number;
  label?: string;
}) {
  if (!data || data.length === 0) return <NoData label={label} />;
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
        <XAxis dataKey={xKey} {...axisProps} />
        <YAxis {...axisProps} allowDecimals={false} />
        <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'hsl(var(--accent) / 0.4)' }} />
        <Bar dataKey={yKey} radius={[4, 4, 0, 0]}>
          {data.map((entry, i) => {
            let fill = color;
            if (colorBy === 'severity') fill = severityColor(entry[xKey]);
            else if (colorBy === 'verdict') fill = verdictColor(entry[xKey]);
            else fill = CHART_COLORS[i % CHART_COLORS.length];
            return <Cell key={i} fill={fill} />;
          })}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function DonutChart({
  data,
  nameKey,
  valueKey,
  colorBy,
  height = 240,
  label,
}: {
  data?: any[];
  nameKey: string;
  valueKey: string;
  colorBy?: 'severity' | 'verdict';
  height?: number;
  label?: string;
}) {
  if (!data || data.length === 0) return <NoData label={label} />;
  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={data}
          dataKey={valueKey}
          nameKey={nameKey}
          innerRadius={55}
          outerRadius={85}
          paddingAngle={2}
          stroke="hsl(var(--card))"
        >
          {data.map((entry, i) => {
            let fill = CHART_COLORS[i % CHART_COLORS.length];
            if (colorBy === 'severity') fill = severityColor(entry[nameKey]);
            else if (colorBy === 'verdict') fill = verdictColor(entry[nameKey]);
            return <Cell key={i} fill={fill} />;
          })}
        </Pie>
        <Tooltip contentStyle={tooltipStyle} />
        <Legend
          iconType="circle"
          wrapperStyle={{ fontSize: 12, color: 'hsl(var(--muted-foreground))' }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function MultiLineChart({
  data,
  xKey,
  lines,
  height = 260,
  label,
}: {
  data?: any[];
  xKey: string;
  lines: { key: string; color: string; name?: string }[];
  height?: number;
  label?: string;
}) {
  if (!data || data.length === 0) return <NoData label={label} />;
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
        <XAxis dataKey={xKey} {...axisProps} />
        <YAxis {...axisProps} />
        <Tooltip contentStyle={tooltipStyle} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {lines.map((l) => (
          <Line
            key={l.key}
            type="monotone"
            dataKey={l.key}
            name={l.name || l.key}
            stroke={l.color}
            strokeWidth={2}
            dot={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

export function HorizontalBarChart({
  data,
  categoryKey,
  valueKey,
  color = '#0ea5e9',
  height = 280,
  label,
}: {
  data?: any[];
  categoryKey: string;
  valueKey: string;
  color?: string;
  height?: number;
  label?: string;
}) {
  if (!data || data.length === 0) return <NoData label={label} />;
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart layout="vertical" data={data} margin={{ top: 5, right: 16, left: 10, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" horizontal={false} />
        <XAxis type="number" {...axisProps} allowDecimals={false} />
        <YAxis type="category" dataKey={categoryKey} {...axisProps} width={120} />
        <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'hsl(var(--accent) / 0.4)' }} />
        <Bar dataKey={valueKey} radius={[0, 4, 4, 0]} fill={color} />
      </BarChart>
    </ResponsiveContainer>
  );
}
