import { NextResponse } from "next/server";
import path from "path";
import fs from "fs/promises";

// T-05-04-A: sanitize name to prevent path traversal before path.join
export async function GET(
  _req: Request,
  { params }: { params: Promise<{ name: string }> },
) {
  const { name } = await params;
  const safe = name.replace(/[^a-zA-Z0-9_.-]/g, "");
  const filePath = path.join(process.cwd(), "public", "traces", safe);
  try {
    const content = await fs.readFile(filePath, "utf-8");
    return new NextResponse(content, {
      headers: { "Content-Type": "application/json" },
    });
  } catch (err: unknown) {
    const code = (err as NodeJS.ErrnoException).code;
    if (code === "ENOENT") {
      return NextResponse.json({ error: "trace not found" }, { status: 404 });
    }
    return NextResponse.json({ error: "server error" }, { status: 500 });
  }
}
