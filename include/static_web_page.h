#pragma once
#include <ESPAsyncWebServer.h>

// The char* send_P overload in our web library builds an AsyncBasicResponse
// and copies the whole page into String. Use the explicit buffer/length
// overload instead: AsyncProgmemResponse reads directly from static flash.
// No template processor: CSS percentages and JavaScript must pass unchanged.
template <size_t N>
void sendStaticWebPage(AsyncWebServerRequest *request, const char (&page)[N]) {
    static_assert(N > 1, "A web page must not be empty");
    AsyncWebServerResponse *response = request->beginResponse(
        200, "text/html; charset=utf-8", reinterpret_cast<const uint8_t *>(page), N - 1);
    if (response) response->addHeader("Cache-Control", "no-store");
    // The library closes the connection safely if response allocation failed.
    request->send(response);
}
