// Aplikacja GRAFICZNA: podgląd w czasie rzeczywistym (sf::GraphicalSimulationApp, OpenGL 4.3+).
//
// Klawisze (dodane):  Spacja – start/stop ogona,  ←/→ – skręt (V_bias ∓0.5 ml),
//   ↑/↓ – częstotliwość ±0.25 Hz,  PgUp/PgDn – głębokość zadana −/+0.25 m (włącza regulator).
// Klawisze biblioteki (zachowane): W/S/A/D/Q/Z – kamera, mysz – obrót/przesuwanie widoku,
//   H – panel, C – konsola komunikatów, K – lista klawiszy, Esc – wyjście.
// Kamera jest "przyklejona" do głowy ryby (OpenGLTrackball::GlueToMoving).
//
// Rozmiar okna: Stonefish 1.5 nie obsługuje zmiany rozmiaru okna – bufory renderingu
// (OpenGLPipeline) mają rozmiar ustalony przy starcie, więc po rozciągnięciu albo
// maksymalizacji obraz zostaje w starym rozmiarze lub się rozjeżdża. Dlatego rozmiar
// wybieramy przy starcie (--window SZERxWYS, domyślnie 90% ekranu) i blokujemy zmianę.

#include <Stonefish/core/GraphicalSimulationApp.h>
#include <Stonefish/graphics/IMGUI.h>
#include <Stonefish/graphics/OpenGLTrackball.h>

#include <SDL2/SDL.h>

#include <cstdio>
#include <iostream>

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
                case SDLK_PAGEUP: fm_->ChangeDepthRef(-0.25); break;    // płycej (NED: z maleje)
                case SDLK_PAGEDOWN: fm_->ChangeDepthRef(+0.25); break;  // głębiej
                default: sf::GraphicalSimulationApp::KeyDown(event);    // klawisze biblioteki
            }
        }

        void DoHUD() override
        {
            sf::GraphicalSimulationApp::DoHUD();   // standardowy panel biblioteki (klawisz H)
            if(!glued_ && fm_->Head() != nullptr && fm_->getTrackball() != nullptr)
            {
                fm_->getTrackball()->GlueToMoving(fm_->Head());
                // Kamera domyślnie krąży 5 m od środka – dla ryby 0.5 m za daleko.
                // MouseScroll zmienia promień: r += s·r/15, więc s = 15·(r_nowy/r − 1).
                fm_->getTrackball()->MouseScroll(15.f * (1.2f / 5.f - 1.f));
                glued_ = true;
                LockWindowSize();
            }
            // Nakładka z ASCII (czcionka GUI nie musi mieć polskich znaków).
            const fish::FishStatus s = fm_->Status();
            const float x = (float)getWindowWidth() - 270.f;
            float y = 10.f;
            getGUI()->DoPanel(x, y, 260.f, 205.f);
            char buf[128];
            auto line = [&](const char* fmt, auto... v) {
                std::snprintf(buf, sizeof(buf), fmt, v...);
                getGUI()->DoLabel(x + 8.f, y += 18.f, buf);
            };
            y -= 10.f;
            line("FISH  t = %.1f s", s.t);
            line("speed       %+.3f m/s", s.speed);
            line("depth true  %.3f m", s.depth);
            line("depth meas  %.3f m  ref %.2f %s", s.depthMeas, s.depthRef, s.depthOn ? "" : "(off)");
            line("tail %s  f = %.2f Hz", s.rhythmOn ? "ON " : "OFF", s.freq);
            line("V_bias      %+.1f ml %s", s.biasMl, s.headingOn ? "(heading ctrl)" : "");
            line("p_L / p_R   %+.1f / %+.1f kPa", s.pL / 1e3, s.pR / 1e3);
            line("VBS water   %.1f ml", s.vbsMl);
            line("yaw         %+.1f deg", s.yawDeg);
            line("SPACE tail, arrows turn/freq, PgUp/Dn depth");
        }

    private:
        // Okno tworzy biblioteka (wskaźnik jest prywatny), ale DoHUD działa w wątku z jego
        // kontekstem OpenGL, więc znajdujemy je przez SDL_GL_GetCurrentWindow().
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
    catch(const std::exception& e) { std::cerr << "BŁĄD konfiguracji: " << e.what() << "\n"; return 2; }

    sf::RenderSettings r;
    if(args.windowW > 0)
    {
        r.windowW = args.windowW;
        r.windowH = args.windowH;
    }
    else
    {
        // 90% obszaru roboczego ekranu, na którym otworzy się okno (ekran główny),
        // w pikselach logicznych (przy skalowaniu ekranu 125% to mniej niż rozdzielczość fizyczna).
        r.windowW = 1280;
        r.windowH = 800;
        // Uwaga: na Waylandzie SDL podaje rozdzielczość FIZYCZNĄ ekranu, a kompozytor traktuje
        // rozmiar okna jako LOGICZNY. Przy skalowaniu 125% okno "90% ekranu" wychodziło poza
        // ekran i było dodatkowo rozciągane. Skalę ekranu bierzemy z DPI (96 DPI = 100%).
        SDL_Rect b;
        if(SDL_InitSubSystem(SDL_INIT_VIDEO) == 0 && SDL_GetDisplayUsableBounds(0, &b) == 0)
        {
            float dpi = 96.f;
            const float scale = (SDL_GetDisplayDPI(0, &dpi, nullptr, nullptr) == 0 && dpi > 96.f) ? dpi / 96.f : 1.f;
            r.windowW = (int)(0.9 * b.w / scale);
            r.windowH = (int)(0.9 * b.h / scale);
        }
    }
    std::cout << "Okno " << r.windowW << "x" << r.windowH << " (zmiana: --window SZERxWYS; rozciąganie okna jest zablokowane)\n";
    r.aa = sf::RenderQuality::HIGH;
    sf::HelperSettings h;
    h.showCoordSys = false;
    h.showJoints = false;
    h.showActuators = false;
    h.showSensors = false;

    FishSimManager mgr(cfg);
    if(!args.outFile.empty())
        mgr.SetLogPath(args.outFile);
    FishGuiApp app(args.rootDir + "/data/", r, h, &mgr);
    try { app.Run(); }
    catch(const std::exception& e) { std::cerr << "BŁĄD: " << e.what() << "\n"; return 1; }
    return 0;
}
