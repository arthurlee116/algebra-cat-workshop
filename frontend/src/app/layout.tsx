import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "魔法整式训练营",
  description: "上海七年级整式练习、积分系统与虚拟猫咪激励平台",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-Hans">
      <body className="antialiased bg-slate-50">
        {children}
      </body>
    </html>
  );
}
