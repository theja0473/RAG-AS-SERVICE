interface StatusBadgeProps {
  status: boolean;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <div className="flex items-center gap-2">
      <div
        className={`w-2.5 h-2.5 rounded-full ${
          status ? 'bg-green-500 animate-pulse' : 'bg-red-500'
        }`}
      />
      <span className={`text-sm font-medium ${status ? 'text-green-400' : 'text-red-400'}`}>
        {status ? 'Online' : 'Offline'}
      </span>
    </div>
  );
}
