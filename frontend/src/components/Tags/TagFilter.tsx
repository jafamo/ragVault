import { useThemeStore } from "../../stores/themeStore";

const TAGS = [
  { name: "legal", count: 12 },
  { name: "técnico", count: 23 },
  { name: "financiero", count: 8 },
  { name: "rrhh", count: 5 },
  { name: "marketing", count: 3 },
];

export default function TagFilter() {
  const skin = useThemeStore((s) => s.skin);

  return (
    <div className="tag-strip">
      {TAGS.map((tag) =>
        skin === "terminal" ? (
          <span className="tag-chip" key={tag.name}>
            #{tag.name}
            <b>({tag.count})</b>
          </span>
        ) : (
          <span className="tag-chip" key={tag.name}>
            <strong>{tag.name}</strong> {tag.count}
          </span>
        )
      )}
    </div>
  );
}
