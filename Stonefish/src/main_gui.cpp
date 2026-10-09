// GRAPHICAL application: real-time view (sf::GraphicalSimulationApp, OpenGL 4.3+).
//
// Keys (added):  Space – start/stop tail,  ←/→ – turn (V_bias ∓0.5 ml),
//   ↑/↓ – frequency ±0.25 Hz,  PgUp/PgDn – reference depth −/+0.25 m (enables the controller).
// Library keys (kept): W/S/A/D/Q/Z – camera, mouse – rotate/pan the view,
//   H – panel, C – message console, K – key list, Esc – quit.
// The camera is "glued" to the fish head (OpenGLTrackball::GlueToMoving).
//
// Window size: Stonefish 1.5 does not support window resizing – the render buffers
// (OpenGLPipeline) have a size fixed at startup, so after stretching or
// maximizing the image stays at the old size or gets distorted. That is why the size
// is chosen at startup (--window WxH, default 90% of the screen) and resizing is locked.

#include <Stonefish/core/GraphicalSimulationApp.h>
#include <Stonefish/graphics/IMGUI.h>
#include <Stonefish/graphics/OpenGLTrackball.h>

#include <SDL2/SDL.h>

#include <algorithm>
#include <cstdio>
#include <iostream>
#include <string>

#include "AppArgs.h"
#include "FishSimManager.h"

namespace
{
    class FishGuiApp : public sf::GraphicalSimulationApp
    {
    public:
        FishGuiApp(const std::string& dataDir, sf::RenderSettings r, sf::HelperSettings h, fish::FishSimManager* m)
            : sf::GraphicalSimulationApp("Fish Stonefish demo", dataDir, r, h, m), fm_(m) {}

        void KeyDown(SDL_Event* event) override
        {
            switch(event->key.keysym.sym)
            {
                case SDLK_SPACE: fm_->ToggleRhythm(); break;
                case SDLK_LEFT: fm_->ChangeBias(-0.5e-6); break;
                case SDLK_RIGHT: fm_->ChangeBias(+0.5e-6); break;
                case SDLK_UP: fm_->ChangeFreq(+0.25); break;
                case SDLK_DOWN: fm_->ChangeFreq(-0.25); break;
                case SDLK_PAGEUP: fm_->ChangeDepthRef(-0.25); break;    // shallower (NED: z decreases)
                case SDLK_PAGEDOWN: fm_->ChangeDepthRef(+0.25); break;  // deeper
                default: sf::GraphicalSimulationApp::KeyDown(event);    // library keys
            }
        }

        void DoHUD() override
        {
            sf::GraphicalSimulationApp::DoHUD();   // standard library panel (key H)
            if(!glued_ && fm_->Head() != nullptr && fm_->getTrackball() != nullptr)
            {
                fm_->getTrackball()->GlueToMoving(fm_->Head());
                // By default the camera orbits 5 m from the center – too far for a 0.5 m fish.
                // MouseScroll changes the radius: r += s·r/15, so s = 15·(r_new/r − 1).
                fm_->getTrackball()->MouseScroll(15.f * (1.2f / 5.f - 1.f));
                glued_ = true;
                LockWindowSize();
            }
            // ASCII-only overlay (the GUI font need not have non-ASCII characters).
            // Text scale follows the window height (1.0 at 960 px, 1.5 at 1440 px).
            const fish::FishStatus s = fm_->Status();
            const float k = std::clamp((float)getWindowHeight() / 960.f, 1.f, 2.f);
            const float dy = 18.f * k, w = 330.f * k;
            const float x = (float)getWindowWidth() - w - 10.f;
            float y = 10.f;
            getGUI()->DoPanel(x, y, w, 23.f * dy + 12.f);
            char buf[160];
            auto line = [&](const char* fmt, auto... v) {
                std::snprintf(buf, sizeof(buf), fmt, v...);
                getGUI()->DoLabel(x + 8.f * k, y += dy, buf, glm::vec4(-1.f), k);
            };
            // the GUI font is proportional, so the force table puts each column at its own x
            auto cols = [&](const char* a, const char* b, const char* c) {
                y += dy;
                getGUI()->DoLabel(x + 8.f * k, y, a, glm::vec4(-1.f), k);
                getGUI()->DoLabel(x + 150.f * k, y, b, glm::vec4(-1.f), k);
                getGUI()->DoLabel(x + 240.f * k, y, c, glm::vec4(-1.f), k);
            };
            auto force = [&](const char* name, const fish::ForceFS& f) {
                char a[32], b[32];
                std::snprintf(a, sizeof(a), "%+.1f", 1e3 * f.fwd);
                std::snprintf(b, sizeof(b), "%+.1f", 1e3 * f.side);
                cols(name, a, b);
            };
            y -= 10.f * k;
            line("FISH  t = %.1f s   pace x%.2f", s.t, fm_->getRealtimeFactor());
            line("speed       %+.3f m/s", s.speed);
            line("depth true  %.3f m", s.depth);
            line("depth meas  %.3f m  ref %.2f %s", s.depthMeas, s.depthRef, s.depthOn ? "" : "(off)");
            line("tail %s  f = %.2f Hz", s.rhythmOn ? "ON " : "OFF", s.freq);
            line("V_bias      %+.1f ml %s", s.biasMl, s.headingOn ? "(heading ctrl)" : "");
            line("p_L / p_R   %+.1f / %+.1f kPa", s.pL / 1e3, s.pR / 1e3);
            line("VBS water   %.1f ml", s.vbsMl);
            line("yaw         %+.1f deg", s.yawDeg);
            line("DRIVE");
            line("tail torque %+.0f mN m (hydraulics)", 1e3 * s.tailTorque);
            line("pump u %+.2f   Q %+.1f ml/s", s.u, s.Q * 1e6);
            std::string th = "joints";
            for(double a : s.thetaDeg) { std::snprintf(buf, sizeof(buf), " %+.0f", a); th += buf; }
            line("%s deg", th.c_str());
            cols("WATER FORCES [mN]", "fwd", "side");
            force("head drag", s.dragHead);
            force("tail drag", s.dragTail);
            force("fin drag", s.dragFin);
            force("fin lift", s.finLift);
            force("total", s.water);
            line("fin angle of attack %.0f deg", s.finAlphaDeg);
            line("fwd + = forward, side + = right");
            line("lines: magenta drag, blue buoyancy");
            line("SPACE tail, arrows turn/freq, PgUp/Dn depth");
        }

    private:
        // The window is created by the library (the pointer is private), but DoHUD runs in the thread with its
        // OpenGL context, so we find it via SDL_GL_GetCurrentWindow().
        void LockWindowSize()
        {
            SDL_Window* w = SDL_GL_GetCurrentWindow();
            if(w == nullptr) return;
            const int W = getWindowWidth(), H = getWindowHeight();
            SDL_SetWindowResizable(w, SDL_FALSE);
            SDL_SetWindowMinimumSize(w, W, H);
            SDL_SetWindowMaximumSize(w, W, H);
        }

        fish::FishSimManager* fm_;
        bool glued_ = false;
    };
}

int main(int argc, char** argv)
{
    using namespace fish;
    AppArgs args = AppArgs::Parse(argc, argv);
    Config cfg;
    try { cfg = Config::Load(args.rootDir, args.configFile, args.overrides); }
    catch(const std::exception& e) { std::cerr << "ERROR (config): " << e.what() << "\n"; return 2; }

    sf::RenderSettings r;
    if(args.windowW > 0)
    {
        r.windowW = args.windowW;
        r.windowH = args.windowH;
    }
    else
    {
        // 90% of the usable area of the screen on which the window opens (the primary screen),
        // in logical pixels (at 125% display scaling this is less than the physical resolution).
        r.windowW = 1280;
        r.windowH = 800;
        // Note: on Wayland SDL reports the PHYSICAL screen resolution, while the compositor treats
        // the window size as LOGICAL. At 125% scaling a "90% of the screen" window extended beyond
        // the screen and was additionally stretched. We take the display scale from the DPI (96 DPI = 100%).
        SDL_Rect b;
        if(SDL_InitSubSystem(SDL_INIT_VIDEO) == 0 && SDL_GetDisplayUsableBounds(0, &b) == 0)
        {
            float dpi = 96.f;
            const float scale = (SDL_GetDisplayDPI(0, &dpi, nullptr, nullptr) == 0 && dpi > 96.f) ? dpi / 96.f : 1.f;
            r.windowW = (int)(0.9 * b.w / scale);
            r.windowH = (int)(0.9 * b.h / scale);
        }
    }
    std::cout << "Window " << r.windowW << "x" << r.windowH << " (change: --window WxH; window resizing is locked)\n";
    r.aa = sf::RenderQuality::HIGH;
    sf::HelperSettings h;
    h.showCoordSys = false;
    h.showJoints = false;
    h.showActuators = false;
    h.showSensors = false;
    h.showForces = true;   // library force lines: buoyancy (blue), quadratic drag (magenta), linear drag (cyan)

    FishSimManager mgr(cfg);
    if(!args.outFile.empty())
        mgr.SetLogPath(args.outFile);
    mgr.setRealtimeFactor(args.speed);
    FishGuiApp app(args.rootDir + "/data/", r, h, &mgr);
    try { app.Run(); }
    catch(const std::exception& e) { std::cerr << "ERROR: " << e.what() << "\n"; return 1; }
    return 0;
}
