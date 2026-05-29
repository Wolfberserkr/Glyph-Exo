package com.glyphexo.unreadcount;

import android.app.Service;
import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Typeface;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;

import com.nothing.ketchum.Glyph;
import com.nothing.ketchum.GlyphException;
import com.nothing.ketchum.GlyphMatrixFrame;
import com.nothing.ketchum.GlyphMatrixManager;
import com.nothing.ketchum.GlyphMatrixObject;

public class GlyphCountToy extends Service {

    private static final int MATRIX_SIZE = 25;
    private static final float CX = 12f;
    private static final float CY = 12f;
    private static final float RADIUS = 11f;
    private static final double TRAIL_ARC = Math.PI / 2;  // 90-degree sweep trail
    private static final long RADAR_INTERVAL_MS = 50;     // 20 fps

    private GlyphMatrixManager mGM;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private double radarAngle = 0;
    private boolean running = false;

    // ── Notification count receiver ───────────────────────────────────────────

    private final BroadcastReceiver countReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            refresh();
        }
    };

    // ── Radar animation loop ──────────────────────────────────────────────────

    private final Runnable radarTick = new Runnable() {
        @Override
        public void run() {
            if (!running || NotificationService.getCount() > 0) return;
            radarAngle = (radarAngle + 0.15) % (2 * Math.PI);
            pushBitmap(buildRadarFrame(radarAngle));
            handler.postDelayed(this, RADAR_INTERVAL_MS);
        }
    };

    // ── Service lifecycle ─────────────────────────────────────────────────────

    @Override
    public IBinder onBind(Intent intent) {
        connect();
        return null;
    }

    @Override
    public boolean onUnbind(Intent intent) {
        running = false;
        handler.removeCallbacks(radarTick);
        try { unregisterReceiver(countReceiver); } catch (Exception ignored) {}
        if (mGM != null) {
            mGM.unInit();
            mGM = null;
        }
        return false;
    }

    // ── GlyphMatrix connection ────────────────────────────────────────────────

    private void connect() {
        mGM = GlyphMatrixManager.getInstance(getApplicationContext());
        mGM.init(new GlyphMatrixManager.Callback() {
            @Override
            public void onServiceConnected(ComponentName name) {
                mGM.register(Glyph.DEVICE_23112);
                running = true;
                registerReceiver(
                    countReceiver,
                    new IntentFilter(NotificationService.ACTION_COUNT_CHANGED),
                    RECEIVER_NOT_EXPORTED
                );
                refresh();
            }

            @Override
            public void onServiceDisconnected(ComponentName name) {}
        });
    }

    // ── Display logic ─────────────────────────────────────────────────────────

    private void refresh() {
        handler.removeCallbacks(radarTick);
        int count = NotificationService.getCount();
        if (count == 0) {
            handler.post(radarTick);
        } else {
            pushBitmap(buildCountFrame(count));
        }
    }

    // Large number centered on the 25×25 matrix
    private Bitmap buildCountFrame(int count) {
        String text = count > 99 ? "99+" : String.valueOf(count);

        Bitmap bmp = Bitmap.createBitmap(MATRIX_SIZE, MATRIX_SIZE, Bitmap.Config.ARGB_8888);
        Canvas canvas = new Canvas(bmp);

        Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        paint.setColor(Color.WHITE);
        paint.setTypeface(Typeface.DEFAULT_BOLD);
        paint.setTextAlign(Paint.Align.CENTER);

        if (count < 10)       paint.setTextSize(18f);
        else if (count < 100) paint.setTextSize(11f);
        else                  paint.setTextSize(8f);

        float textY = CY - (paint.descent() + paint.ascent()) / 2f;
        canvas.drawText(text, CX + 0.5f, textY, paint);

        return bmp;
    }

    // Radar sweep: bright rotating arm with a fading 90-degree trail
    private Bitmap buildRadarFrame(double theta) {
        Bitmap bmp = Bitmap.createBitmap(MATRIX_SIZE, MATRIX_SIZE, Bitmap.Config.ARGB_8888);
        Canvas canvas = new Canvas(bmp);

        // Trail — drawn back-to-front so the arm tip is brightest
        for (double t = theta - TRAIL_ARC; t <= theta; t += 0.04) {
            float alpha = (float) ((t - (theta - TRAIL_ARC)) / TRAIL_ARC);
            Paint p = new Paint();
            p.setColor(Color.argb((int) (alpha * 210), 255, 255, 255));
            for (float r = 2f; r <= RADIUS; r += 0.7f) {
                float x = CX + r * (float) Math.cos(t);
                float y = CY + r * (float) Math.sin(t);
                int px = Math.round(x), py = Math.round(y);
                if (px >= 0 && px < MATRIX_SIZE && py >= 0 && py < MATRIX_SIZE) {
                    canvas.drawPoint(px, py, p);
                }
            }
        }

        // Bright sweep arm
        Paint arm = new Paint(Paint.ANTI_ALIAS_FLAG);
        arm.setColor(Color.WHITE);
        arm.setStrokeWidth(1.5f);
        float tx = CX + RADIUS * (float) Math.cos(theta);
        float ty = CY + RADIUS * (float) Math.sin(theta);
        canvas.drawLine(CX, CY, tx, ty, arm);

        // Centre dot
        arm.setStrokeWidth(3f);
        canvas.drawPoint(CX, CY, arm);

        return bmp;
    }

    // ── SDK push ──────────────────────────────────────────────────────────────

    private void pushBitmap(Bitmap bmp) {
        if (mGM == null || !running) return;
        try {
            GlyphMatrixObject obj = new GlyphMatrixObject.Builder()
                .setImageSource(bmp)
                .setBrightness(255)
                .build();

            GlyphMatrixFrame frame = new GlyphMatrixFrame.Builder()
                .addTop(obj)
                .build(this);

            mGM.setMatrixFrame(frame.render());
        } catch (GlyphException ignored) {}
    }
}
