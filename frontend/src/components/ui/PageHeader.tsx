type PageHeaderProps = {
  eyebrow?: string;
  title: string;
  description?: string;
};

function PageHeader({
  eyebrow,
  title,
  description,
}: PageHeaderProps) {
  return (
    <div>
      {eyebrow && (
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-lime-soft">
          {eyebrow}
        </p>
      )}

      <h1 className="mt-3 font-display text-5xl font-bold tracking-[-0.05em] text-white">
        {title}
      </h1>

      {description && (
        <p className="mt-5 max-w-2xl text-lg leading-8 text-copy-muted">
          {description}
        </p>
      )}
    </div>
  );
}

export default PageHeader;