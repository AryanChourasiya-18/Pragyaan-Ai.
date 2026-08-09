import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";

export default function Layout() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 px-10 py-8 max-w-6xl">
        <Outlet />
      </main>
    </div>
  );
}
