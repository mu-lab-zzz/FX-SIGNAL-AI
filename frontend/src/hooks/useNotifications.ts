import { useCallback, useEffect, useState } from "react";

export function useNotifications() {
  const [permission, setPermission] = useState<NotificationPermission>("default");

  useEffect(() => {
    if ("Notification" in window) {
      setPermission(Notification.permission);
    }
  }, []);

  const requestPermission = useCallback(async () => {
    if (!("Notification" in window)) return false;
    const result = await Notification.requestPermission();
    setPermission(result);
    return result === "granted";
  }, []);

  const notify = useCallback(
    (title: string, body: string, icon = "/favicon.ico") => {
      if (permission !== "granted") return;
      try {
        new Notification(title, { body, icon });
      } catch {}
    },
    [permission]
  );

  return { permission, requestPermission, notify };
}
