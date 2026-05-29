package com.glyphexo.unreadcount;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.os.Bundle;
import android.provider.Settings;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;

public class MainActivity extends Activity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Button notifButton = findViewById(R.id.notifButton);
        Button toysButton = findViewById(R.id.toysButton);

        notifButton.setOnClickListener(v ->
            startActivity(new Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)));

        toysButton.setOnClickListener(v -> {
            try {
                Intent intent = new Intent();
                intent.setComponent(new ComponentName(
                    "com.nothing.thirdparty",
                    "com.nothing.thirdparty.matrix.toys.manager.ToysManagerActivity"
                ));
                startActivity(intent);
            } catch (Exception ignored) {
                startActivity(new Intent(Settings.ACTION_SETTINGS));
            }
        });
    }

    @Override
    protected void onResume() {
        super.onResume();
        TextView status = findViewById(R.id.statusText);
        Button notifButton = findViewById(R.id.notifButton);

        if (isNotificationAccessGranted()) {
            status.setText("Ready! Tap below to add Unread Count to your Glyph Toys.");
            notifButton.setVisibility(View.GONE);
        } else {
            status.setText("Step 1: grant notification access so the app can count your alerts.");
            notifButton.setVisibility(View.VISIBLE);
        }
    }

    private boolean isNotificationAccessGranted() {
        String flat = Settings.Secure.getString(
            getContentResolver(), "enabled_notification_listeners");
        if (flat == null) return false;
        for (String name : flat.split(":")) {
            ComponentName cn = ComponentName.unflattenFromString(name);
            if (cn != null && getPackageName().equals(cn.getPackageName())) return true;
        }
        return false;
    }
}
