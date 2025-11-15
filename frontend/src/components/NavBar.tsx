"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useEffect, useRef } from "react";
import { StoredUser } from "@/lib/userStorage";

const LINKS = [
  { href: "/practice", label: "做题" },
  { href: "/cat", label: "我的猫" },
];

type Props = {
  user: StoredUser | null;
  onLogout: () => void;
};

export default function NavBar({ user, onLogout }: Props) {
  const pathname = usePathname();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scoreAnimation, setScoreAnimation] = useState<'up' | 'down' | null>(null);
  const prevScoreRef = useRef<number | null>(null);

  const handleNavigate = (href: string) => {
    setMobileOpen(false);
    router.push(href);
  };

  // 监听积分变化
  useEffect(() => {
    if (!user) {
      prevScoreRef.current = null;
      setScoreAnimation(null);
      return;
    }

    const currentScore = user.total_score;
    const previousScore = prevScoreRef.current;
    prevScoreRef.current = currentScore;

    if (previousScore === null || currentScore === previousScore) {
      return;
    }

    const change = currentScore - previousScore;
    setScoreAnimation(change > 0 ? "up" : "down");

    const timer = setTimeout(() => {
      setScoreAnimation(null);
    }, 2000);

    return () => clearTimeout(timer);
  }, [user]);

  return (
    <header className="bg-white shadow-sm sticky top-0 z-30">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <div className="flex items-center gap-6">
          <span className="text-lg font-semibold text-purple-700">魔法整式训练营</span>
          <nav className="hidden sm:flex items-center gap-3 text-sm font-medium">
            {LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-full px-4 py-2 transition ${
                  pathname === link.href
                    ? "bg-purple-100 text-purple-700"
                    : "text-gray-600 hover:bg-purple-50"
                }`}
              >
                {link.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-3 text-sm">
          {user ? (
            <div className="text-right">
              <p className="font-semibold text-gray-900">
                {user.chinese_name} · {user.class_name}
              </p>
              <div className={`text-xs text-gray-500 transition-all duration-500 ${
                scoreAnimation === 'up' ? 'text-green-600 font-semibold' :
                scoreAnimation === 'down' ? 'text-red-600 font-semibold' : ''
              }`}>
                总积分：
                <span className={`inline-block transition-all duration-500 ${
                  scoreAnimation === 'up' ? 'scale-110' :
                  scoreAnimation === 'down' ? 'scale-95' : 'scale-100'
                }`}>
                  {user.total_score}
                </span>
                {scoreAnimation === 'up' && (
                  <span className="ml-1 text-green-500">↑</span>
                )}
                {scoreAnimation === 'down' && (
                  <span className="ml-1 text-red-500">↓</span>
                )}
              </div>
            </div>
          ) : (
            <p className="text-xs text-gray-500">未登录</p>
          )}
          <button
            onClick={() => {
              setMobileOpen((prev) => !prev);
            }}
            className="sm:hidden rounded-full border border-purple-200 px-3 py-1 text-xs text-purple-700"
          >
            菜单
          </button>
          <button
            onClick={onLogout}
            className="hidden rounded-full border border-red-200 px-4 py-2 text-xs font-semibold text-red-600 transition hover:bg-red-50 sm:inline-flex"
          >
            退出
          </button>
        </div>
      </div>
      {mobileOpen && (
        <div className="sm:hidden border-t border-purple-100 bg-white px-4 py-2 text-sm">
          <div className="flex flex-col gap-2">
            {LINKS.map((link) => (
              <button
                key={link.href}
                className={`rounded-lg px-3 py-2 text-left ${
                  pathname === link.href ? "bg-purple-100 text-purple-700" : "text-gray-700"
                }`}
                onClick={() => handleNavigate(link.href)}
              >
                {link.label}
              </button>
            ))}
            <button
              onClick={onLogout}
              className="rounded-lg border border-red-200 px-3 py-2 text-left text-red-600"
            >
              退出当前账号
            </button>
          </div>
        </div>
      )}
    </header>
  );
}
