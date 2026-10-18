"""Output-stage research tools, with no implied YM3420 DAC specification.

The resistor/opamp noise calculation uses the documented PSS-480 network.
DAC precision, summed-DAC placement, voltage scale and 48 kHz hold are explicit
sensitivity hypotheses. These are not enabled by the FM engine defaults.
"""
import numpy as np
from scipy import signal
from .model import build_pss480_circuit

KB = 1.380649e-23


def noise_spectrum(hz, temperature_kelvin=300., opamp_en=10e-9):
    """One-sided output voltage-noise covariance (V²/Hz), including L/R sharing.

    Every physical resistor: Norton PSD 4*k*T/R. Every opamp: independent
    white input voltage noise, 10 nV/sqrt(Hz) manufacturer typical. Equivalent
    opamp input resistances are not additional physical Johnson-noise sources.
    Excludes current noise, 1/f noise, DAC, BBD, supply and recording noise.
    """
    f = np.atleast_1d(hz).astype(float)
    if (f.ndim != 1 or not len(f) or not np.isfinite(f).all() or np.any(f <= 0)
            or not np.isfinite(temperature_kelvin) or temperature_kelvin <= 0
            or not np.isfinite(opamp_en) or opamp_en < 0):
        raise ValueError('Positive frequencies/temperature and nonnegative noise required')
    c, _ = build_pss480_circuit()
    sources = []
    for part in c.parts:
        b = np.zeros(len(c.G))
        if part['kind'] == 'R' and not part['name'].endswith('_Rin'):
            for node, sign in ((part['a'], 1), (part['b'], -1)):
                if node != '0': b[c.ids[node]] += sign
            density = 4 * KB * temperature_kelvin / part['value']
        elif part['kind'] == 'opamp':
            b[c.names.index('I_' + part['name'])] = part['dc_gain']
            density = opamp_en ** 2
        else:
            continue
        sources.append((part['name'], b * np.sqrt(density)))
    injection = np.column_stack([b for _, b in sources])
    transfer = np.stack([np.linalg.solve(c.G + 2j*np.pi*x*c.C, injection)
        [[c.ids['volume_top_l'], c.ids['volume_top_r']], :] for x in f])
    covariance = np.einsum('fcs,fds->fcd', transfer, transfer.conj())
    components = {name: abs(transfer[:, 0, i])**2 for i, (name, _) in enumerate(sources)}
    return covariance, components


def stationary_noise(n, sr, hz, covariance, seed=780):
    """Deterministic stationary stereo noise from a one-sided covariance curve.

    Frequency-domain synthesis preserves the shared buffer noise between L/R.
    Band-limit to the supplied measured/calculated frequency range; no looping
    recording or reference samples are used.
    """
    if isinstance(n, bool) or not isinstance(n, (int, np.integer)) or n < 2:
        raise ValueError('At least two integer samples required')
    if not np.isfinite(sr) or sr <= 0: raise ValueError('Positive finite sample rate required')
    hz = np.asarray(hz, dtype=float)
    covariance = np.asarray(covariance, dtype=complex)
    if (hz.ndim != 1 or len(hz) < 2 or not np.isfinite(hz).all()
            or hz[0] < 0 or np.any(np.diff(hz) <= 0)):
        raise ValueError('Finite strictly increasing nonnegative frequency grid required')
    if covariance.shape != (len(hz), 2, 2) or not np.isfinite(covariance).all():
        raise ValueError('Finite frequency x 2 x 2 covariance required')
    scale = max(float(np.max(abs(covariance))), np.finfo(float).tiny)
    if np.max(abs(covariance-covariance.conj().swapaxes(1,2))) > 1e-10*scale:
        raise ValueError('Covariance must be Hermitian')
    if np.min(np.linalg.eigvalsh(covariance)) < -1e-10*scale:
        raise ValueError('Covariance must be positive semidefinite')
    f = np.fft.rfftfreq(n, 1/sr)
    psd = np.zeros((len(f), 2, 2), dtype=complex)
    for a in range(2):
        for b in range(2):
            psd[:, a, b] = np.interp(f, hz, covariance[:, a, b].real, left=0, right=0) + 1j*np.interp(f, hz, covariance[:, a, b].imag, left=0, right=0)
    # Hermitian eigendecomposition also handles perfectly correlated channels.
    values, vectors = np.linalg.eigh(psd)
    root = vectors * np.sqrt(np.maximum(values, 0))[:, None, :]
    white = np.fft.rfft(np.random.default_rng(seed).standard_normal((n, 2)), axis=0)
    spectrum = np.einsum('fij,fj->fi', root, white) * np.sqrt(sr/2)
    spectrum[0] = 0
    if n % 2 == 0: spectrum[-1] = 0
    return np.fft.irfft(spectrum, n=n, axis=0)


def dac_sensitivity(audio, sr=48000, bits=None, full_scale_peak=1., oversample=4):
    """Hypothesis: one linear DAC AFTER the sum, held for one simulation sample.

    No YM3420 bit depth or hardware sample rate is asserted. A common full-scale
    setting must be used for the whole performance, never fitted per preset.
    Quantization is undithered and saturating. This differs intentionally from
    the old per-voice `output_bits` oscillator experiment.
    """
    x = np.asarray(audio, dtype=float)
    if x.ndim != 1 or not np.isfinite(x).all(): raise ValueError('Finite mono signal required')
    if (not np.isfinite(full_scale_peak) or full_scale_peak <= 0 or not np.isfinite(sr) or sr <= 0
            or isinstance(oversample, bool) or not isinstance(oversample,(int,np.integer)) or oversample < 2):
        raise ValueError('Invalid DAC parameters')
    if bits is not None:
        if isinstance(bits,bool) or not isinstance(bits, (int,np.integer)) or not 2 <= bits <= 24: raise ValueError('bits must be 2..24')
        step = 2 * full_scale_peak / 2**bits
        x = np.clip(np.rint(x / step), -2**(bits-1), 2**(bits-1)-1) * step
    if not len(x): return x.copy()
    high = np.repeat(x, oversample)  # zero-order hold, not ideal interpolation
    circuit, out = build_pss480_circuit()
    high = circuit.process(high, sr * oversample, out)
    return signal.resample_poly(high, 1, oversample)[:len(x)]
