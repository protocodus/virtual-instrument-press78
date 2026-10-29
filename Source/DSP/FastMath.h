#pragma once
#include <cmath>

// Inline kernels for the engine's per-tick transcendentals. They replace a
// libm call (out of line, and in the Rack's -fno-builtin build the SDK's own
// software routine) by a few dozen inline operations. Each differs from libm
// by at most a few units in the last place; the maximum error over its domain
// is written beside it (swept against glibc on 2^24 points, 2026-10-29).
// A one-ulp error in every oscillator stays below -180 dB on every shipped
// Rack patch (Docs/benchmarks/cpu-2026-10-29.md).
namespace press78::fast_math {

// fdlibm's __kernel_sin and __kernel_cos on |x| <= pi/4, without the
// reduction tail, which a 33+53-bit Cody-Waite reduction does not produce.
inline double sinKernel(double x) noexcept {
    constexpr double s1 = -1.66666666666666324348e-01, s2 = 8.33333333332248946124e-03,
                     s3 = -1.98412698298579493134e-04, s4 = 2.75573137070700676789e-06,
                     s5 = -2.50507602534068634195e-08, s6 = 1.58969099521155010221e-10;
    const double z = x * x;
    return x + z * x * (s1 + z * (s2 + z * (s3 + z * (s4 + z * (s5 + z * s6)))));
}
inline double cosKernel(double x) noexcept {
    constexpr double c1 = 4.16666666666666019037e-02, c2 = -1.38888888888741095749e-03,
                     c3 = 2.48015872894767294178e-05, c4 = -2.75573143513906633035e-07,
                     c5 = 2.08757232129817482790e-09, c6 = -1.13596475577881948265e-11;
    const double z = x * x;
    const double r = z * (c1 + z * (c2 + z * (c3 + z * (c4 + z * (c5 + z * c6)))));
    const double hz = 0.5 * z, w = 1.0 - hz;
    return w + (((1.0 - w) - hz) + z * r);
}

// sin(x) for |x| < 2^19: x less its nearest multiple of pi/2, split so
// n * pio2Hi is exact. Within 1.1e-16 of glibc on [-1000, 1000]; anything
// larger or non-finite goes to std::sin.
inline double sin(double x) noexcept {
    constexpr double invPio2 = 6.36619772367581382433e-01;
    constexpr double pio2Hi = 1.57079632673412561417e+00, pio2Lo = 6.07710050650619224932e-11;
    if (!(x > -524288.0 && x < 524288.0)) return std::sin(x);
    const double q = x * invPio2;
    const int n = static_cast<int>(q >= 0.0 ? q + 0.5 : q - 0.5);
    const double fn = static_cast<double>(n);
    const double r = (x - fn * pio2Hi) - fn * pio2Lo;
    switch (n & 3) {
    case 0: return sinKernel(r);
    case 1: return cosKernel(r);
    case 2: return -sinKernel(r);
    default: return -cosKernel(r);
    }
}

} // namespace press78::fast_math
