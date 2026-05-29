package com.glyphexo.unreadcount;

import android.app.Notification;
import android.content.Intent;
import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;

public class NotificationService extends NotificationListenerService {

    static final String ACTION_COUNT_CHANGED = "com.glyphexo.unreadcount.COUNT_CHANGED";
    private static volatile int sCount = 0;

    static int getCount() { return sCount; }

    @Override
    public void onListenerConnected() {
        recount();
    }

    @Override
    public void onNotificationPosted(StatusBarNotification sbn) {
        recount();
    }

    @Override
    public void onNotificationRemoved(StatusBarNotification sbn) {
        recount();
    }

    private void recount() {
        int count = 0;
        StatusBarNotification[] active = getActiveNotifications();
        if (active != null) {
            for (StatusBarNotification sbn : active) {
                Notification n = sbn.getNotification();
                boolean clearable = (n.flags & Notification.FLAG_NO_CLEAR) == 0
                                 && (n.flags & Notification.FLAG_ONGOING_EVENT) == 0;
                if (clearable) count++;
            }
        }
        sCount = count;
        sendBroadcast(new Intent(ACTION_COUNT_CHANGED));
    }
}
