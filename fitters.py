from scipy.optimize import curve_fit
import numpy as np
import inspect
from scipy.stats import chi2
from scipy.special import wofz


class Fitter:
    # generic fitter class that contains all the fitting functions
    # delegates the fitting task to the correct fitting function
    def __init__(self, func=None):
        self.fit_functions = {'linear': fit_linear(),
                              'Gaussian': fit_Gaussian(),
                              'Lorentzian': fit_Lorentzian(),
                              'tracker': fit_tracker(),
                              'sin': fit_sin(),
                              'n15': fit_n15(),
                              'exp': fit_exp(),
                              'exp_offset': fit_exp_offset(),
                              'power': fit_power(),
                              'power_offset': fit_power_offset(),
                              'satcurve': fit_satcurve()}

        self.fitter = None
        if func is not None:
            self.set_function(func)

    def set_function(self, func):
        if func in self.fit_functions.keys():
            self.fitter = self.fit_functions[func]

    def set_fp(self, fp):
        self.fitter.fp = fp

    def dofit(self):
        return self.fitter.dofit()

    def set_guess(self, guess):
        self.fitter.set_guess(guess)

    def set_bounds(self, bounds):
        self.fitter.set_bounds(bounds)

    def set_fixed(self, params):
        self.fitter.set_fixed(params)

    def set_data(self, data, xvals=None):
        self.fitter.set_data(data, xvals)

    def model(self, *args, **kwargs):
        '''empty function to be filled by daughter classes'''
        return self.fitter.model(args, kwargs)

    def func(self):
        return self.fitter.func()

    def params(self):
        return self.fitter.params

    def name(self):
        return self.fitter.name()

    def get_fitcurve(self, xvals=None):
        return self.fitter.get_fitcurve(xvals)

    def get_fitcurve_smooth(self, n=100):
        return self.fitter.get_fitcurve_smooth(n)

    def get_guess(self):
        return self.fitter.get_guess()


class GenericFit:
    # parent class for the generic fitter
    def __init__(self, data=None, xvals=None):
        if xvals is None and data is not None:
            xvals = range(len(data))
        self.fp = np.array([])
        self.cov = np.array([])
        self.err = np.array([])
        self.guess = np.array([])
        self.data = np.array(data)
        self.xvals = np.array(xvals)
        self.yerr = None
        # bool extguess is true when user externally provides guess
        self.extguess = False
        self.bounds = (-np.inf, np.inf)

        # save lists of parameters
        sig = inspect.signature(self.model)
        params = list(sig.parameters.keys())
        self.params = params[1:]

    def set_fp(self, fp):
        self.fp = fp

    def dofit(self, *args, **kwargs):
        _nanlocs = np.where(np.isnan(self.data))
        self.xvals = np.delete(self.xvals, _nanlocs)
        self.data = np.delete(self.data, _nanlocs)

        if not self.extguess:
            self.get_guess()

        self.fp, self.cov = curve_fit(self.model,
                                      self.xvals, self.data,
                                      bounds=self.bounds,
                                      sigma=self.yerr,
                                      p0=self.guess)

        self.err = np.sqrt(np.diag(self.cov))

        # params = self.params()
        # for i in range(len(params)):
        #     print('%s: %.3e' % (params[i], self.fp[i]))

        return self.fp

    def set_guess(self, guess):
        # if the user feels intelligent, give option
        # to set initial guess outside the function
        self.extguess = True
        self.guess = guess

    def set_bounds(self, bounds):
        # bounds should be in the forms of ([lower_bounds], [upper_bounds])
        self.bounds = bounds

    def set_fixed(self, params):
        if len(params) != len(self.params):
            print('Error: set_fixed(params) - params dimension not matched.')
        else:
            bounds_lo = []
            bounds_hi = []

            for p in params:
                if p is None:
                    bounds_lo.append(-np.inf)
                    bounds_hi.append(np.inf)
                else:
                    bounds_lo.append(float(p)-np.finfo(float).eps)
                    bounds_hi.append(float(p)+np.finfo(float).eps)

            self.set_bounds((bounds_lo, bounds_hi))

            # take care of guess out of bounds - todo: move this to dofit
            self.set_guess(self.get_guess())
            for i in range(len(params)):
                if params[i] is not None:
                    self.guess[i] = params[i]

    def set_data(self, data, xvals=None):
        self.data = np.array(data)
        if xvals is None:
            self.xvals = np.array(range(len(data)))
        else:
            self.xvals = np.array(xvals)
            
    def set_err(self, err):
        self.yerr = err

    def model(self, *args, **kwargs):
        '''empty function to be filled by daughter classes'''
        return None

    def func(self):
        return ''

    def name(self):
        return self.__class__.__name__.replace('fit_', '')
    
    def get_chisq(self, reduced=False):
        if self.yerr is None:
            raise Exception('yerr is not defined.')
        else:
            chisq = np.sum(np.power(np.divide(self.data - self.get_fitcurve(), self.yerr),2))
            if reduced:
                chisq /= (len(self.data) - len(self.fp))
                
        return chisq
    
    def get_pval(self):
        return 1 - chi2.cdf(self.get_chisq(), len(self.data)-len(self.fp))

    def get_fitcurve(self, xvals=None):
        if xvals is None:
            xvals = self.xvals
        return self.model(xvals, *list(self.fp))

    def get_fitcurve_smooth(self, n=100):
        xvals = np.linspace(self.xvals[0], self.xvals[-1], n+1)
        return [xvals, self.model(xvals, *list(self.fp))]

    def get_guess(self):
        return self.guess


class fit_Gaussian(GenericFit):
    # Gaussian Fit
    def __init__(self, data=None, xvals=None):
        super().__init__(data, xvals)

    def func(self):
        return 'amp * exp(-(x-x0)**2/(2*sigma**2)) + offset'

    def model(self, x, amp, x0, sigma, offset):
        # gaussian constrained to positive amp guesses by squaring the amplitude
        func = amp * np.exp(-(x-x0)**2/(2*sigma**2)) + offset
        return func

    def get_guess(self):
        offset = np.mean(self.data)
        maxval = np.amax(self.data)
        minval = np.amin(self.data)
        if maxval - offset > offset - minval:
            # positive amplitude
            x0 = self.xvals[np.argmax(self.data)]
            amp = maxval - offset
        else:
            x0 = self.xvals[np.argmin(self.data)]
            amp = minval - offset

        ind_hwhm = np.argmin(np.abs((self.data - offset) - amp / 2))
        sigma = np.abs(self.xvals[ind_hwhm] - x0)

        self.guess = [amp, x0, sigma, offset]
        self.set_bounds()
        return self.guess

    def set_bounds(self, bounds=None):
        if bounds is None:
            bounds = ([-np.Inf, -np.Inf, 0, -np.Inf],
                      [np.Inf, np.Inf, np.Inf, np.Inf])
        self.bounds = bounds


class fit_tracker(GenericFit):
    '''
    currently used by the tracker to find the center of the NV using PL
    '''
    def __init__(self, data=None, xvals=None):
        super().__init__(data, xvals)

    def model(self, x, amp, x0, sigma, offset):
        # gaussian constrained to positive amp guesses by squaring the amplitude
        func = amp**2 * np.exp(-(x-x0)**2/(2*sigma**2)) + offset
        return func

    def get_guess(self):
        amplitude = np.sqrt(self.data.max())
        peakcenter = self.xvals[np.argmax(self.data)]

        minfunc = self.data - amplitude/2
        index = np.argmin(np.abs(minfunc))

        sigma = np.abs(peakcenter-self.xvals[index])
        mean = np.mean(self.data)

        self.guess = [amplitude, peakcenter, sigma, mean]
        return self.guess

    def get_peakcenter(self):
        '''
        specific function used by the nv tracker
        Returns: peak center as per the x axis given by xvals
        '''
        return self.fp[1]

    def get_peakwidth(self):
        return self.fp[2]


class fit_tracker_z(GenericFit):
    '''
    currently used by the tracker to find the center of the NV using PL
    '''
    def __init__(self, data=None, xvals=None):
        super().__init__(data, xvals)

    def model(self, x, amp_1, x0_1, sigma_1, amp_2, x0_2, sigma_2, offset):
        # gaussian constrained to positive amp guesses by squaring the amplitude
        func = amp_1**2 * np.exp(-(x-x0_1)**2/(2*sigma_1**2)) + amp_2**2 * np.exp(-(x-x0_2)**2/(2*sigma_2**2)) + offset
        return func

    def get_guess(self):
        amplitude = np.sqrt(self.data.max())
        peakcenter = self.xvals[np.argmax(self.data)]

        minfunc = self.data - amplitude/2
        index = np.argmin(np.abs(minfunc))

        sigma = np.abs(peakcenter-self.xvals[index])
        offset = self.data.min()

        self.guess = [0.9*amplitude, peakcenter, 0.8*sigma, 0.9*amplitude*0.8, peakcenter + 1, sigma, offset]
        return self.guess

    def get_peakcenter(self):
        '''
        specific function used by the nv tracker
        Returns: peak center as per the x axis given by xvals
        '''
        return min(self.fp[1], self.fp[4])

    def get_peakwidth(self):
        return self.fp[2]

class fit_linear(GenericFit):
    def __init__(self, data=None, xvals=None):
        super().__init__(data, xvals)

    def func(self):
        return 'a + b*x'

    def model(self, x, a, b):
        func = a + b*x
        return func

    def get_guess(self):
        a = np.mean(self.data)
        b = (self.data[-1] - self.data[0]) / (self.xvals[-1] - self.xvals[0])
        self.guess = [a, b]
        return self.guess


class fit_Lorentzian(GenericFit):
    def __init__(self, data=None, xvals=None):
        super().__init__(data, xvals)

    def func(self):
        return 'func = amp * gamma**2/((x - x0)**2 + gamma**2) + offset'

    def model(self, x, amp, x0, gamma, offset):
        numerator = gamma**2
        denominator = (x - x0)**2 + gamma**2
        func = amp * numerator/denominator + offset
        return func

    def get_guess(self):
        offset = np.mean(self.data)
        maxval = np.amax(self.data)
        minval = np.amin(self.data)
        if maxval - offset > offset - minval:
            # positive amplitude
            x0 = self.xvals[np.argmax(self.data)]
            amp = maxval - offset
        else:
            x0 = self.xvals[np.argmin(self.data)]
            amp = minval - offset

        ind_hwhm = np.argmin(np.abs((self.data - offset) - amp/2))
        gamma = np.abs(self.xvals[ind_hwhm] - x0)

        self.guess = np.array([amp, x0, gamma, offset])
        self.set_bounds()
        return self.guess

    def set_bounds(self, bounds=None):
        if bounds is None:
            bounds=([-np.Inf, -np.Inf, 0, -np.Inf],
                    [np.Inf, np.Inf, np.Inf, np.Inf])
        self.bounds = bounds

class fit_Voigt(GenericFit):
    def __init__(self, data=None, xvals=None):
        super().__init__(data, xvals)

    def func(self):
        return 'amp*Voigt(x-x0, alpha, gamma) + offset'

    def model(self, x, amp, x0, alpha, gamma, offset):
        """
        Return the Voigt line shape at x with Lorentzian component HWHM gamma
        and Gaussian component HWHM alpha.

        """
        sigma = alpha / np.sqrt(2 * np.log(2))

        func = amp*np.real(wofz(((x-x0) + 1j * gamma) / sigma / np.sqrt(2))) / sigma / np.sqrt(2 * np.pi) + offset
        return func

    def get_guess(self):
        offset = np.mean(self.data)
        maxval = np.amax(self.data)
        minval = np.amin(self.data)
        if maxval - offset > offset - minval:
            # positive amplitude
            x0 = self.xvals[np.argmax(self.data)]
            amp = maxval - offset
        else:
            x0 = self.xvals[np.argmin(self.data)]
            amp = minval - offset

        ind_hwhm = np.argmin(np.abs((self.data - offset) - amp/2))
        gamma = np.abs(self.xvals[ind_hwhm] - x0)

        # just use same alpha and gamma...good enough for a guess
        self.guess = np.array([amp, x0, gamma, gamma, offset])
        return self.guess
    

class fit_sin(GenericFit):
    def __init__(self, data=None, xvals=None):
        super().__init__(data, xvals)

    def func(self):
        return 'amp * sin(2 * pi * x * f1 + phi1) + offset'

    def model(self, x, amp, f1, phi1, offset):
        func = amp *np.sin(2 * np.pi * x *f1 + phi1) + offset
        return func

    def get_guess(self):
        f1 = self.get_freqpeak(self.xvals, self.data)
        phi1 = np.pi/2
        offset = np.mean(self.data)
        amp = np.max(self.data) - offset
        self.guess = [amp, f1, phi1, offset]
        self.set_bounds()
        return self.guess

    def set_bounds(self, bounds=None):
        if bounds is None:
            bounds = ([-np.Inf, -np.Inf, -1.2*np.pi, -np.Inf], [np.Inf, np.Inf, 1.2*np.pi, np.Inf])
        self.bounds = bounds

    def get_freqpeak(self, xdata, ydata):
        '''
        return the frequency of ydata in appropriate units, as set by xdata
        Args:
            xdata: usually time, assumes uniform period
            ydata: the signal you want the period of
        Returns: returns period in units appropriate to xdata
        '''
        fftdata = np.fft.fft(ydata)
        timestep = np.diff(xdata)[-1]
        # print('assumes uniform sampling interval in calculating FFT')
        freqdata = np.fft.fftfreq(len(ydata), d=timestep)

        halfway = int(np.round(len(fftdata)/2))

        indmax = np.argmax(np.abs(fftdata[1:halfway]))
        indmax += 1

        return freqdata[indmax]

    def get_period(self):
        '''
        useful for calculating the pi, pi/2 etc pulse periods
        Returns: 2 pi pulse period
        '''
        return np.abs(1/self.fp[1])

    def get_pulsetimes(self):
        '''
        useful for giving accurate times for specific rotations when there is a significant phi1 offset
        Returns: timevect for pi/2, pi, and 3pi/2
        '''
        f1 = self.fp[1]
        phi1 = self.fp[2]
        anglevect = [np.pi/2, np.pi, 1.5*np.pi]
        timevect = []
        for angle in anglevect:
            timevect.append((angle - phi1 + np.pi/2) / 2 / np.pi / f1)
        return timevect


class fit_n15(GenericFit):
    def __init__(self, data=None, xvals=None):
        super().__init__(data, xvals)

    def func(self):
        return 'offset - dipdepth*( (1\u00B1pol)/2*np.exp(-(x-x0\u00B1hyperfine/2)**2/sigma**2)'

    def model(self, x, offset, dipdepth, pol, x0, hyperfine, sigma):
        # double peaked gaussian typical of the N-15 spectrum
        func = offset - dipdepth*( (1+pol)/2*np.exp(-(x-x0+hyperfine/2)**2/sigma**2) + (1-pol)/2*np.exp(-(x-x0-hyperfine/2)**2/sigma**2) )
        return func

    def get_guess(self):
        offset = np.mean(self.data)
        hyperfine = 3.03e6  # the N15 hyperfine spectrum guess
        x0 = self.xvals[np.argmin(self.data)] + hyperfine/2
        pol = 0.5
        dipdepth = 0.1*offset
        sigma = 1e6
        self.guess = np.array([offset, dipdepth, pol, x0, hyperfine, sigma])


class fit_c13echodecay(GenericFit):
    def __init__(self, data=None, xvals=None):
        super().__init__(data, xvals)

    def model(self, x, amp, tau, doubleperiod, phaseoffset, yoffset, n):
        f = 1 / doubleperiod
        func = amp * np.exp(-(x / tau) ** n) * (np.cos(2 * np.pi * f * x + phaseoffset)) ** 2 + yoffset
        return func

    def set_bounds(self, bounds=None):
        if bounds is None:
            bounds = ([0.1, 0.5e-6, 1e-6, -1.2*np.pi, 0, 0.5], [1.4, 100e-6, 20e-6, 1.2*np.pi, 1, 2])
        self.bounds = bounds

    def get_guess(self):
        ampguess = 1
        tauguess = 20e-6
        doubleperiodguess = 16e-6
        phaseoffsetguess = 0
        yoffset = np.mean(self.data)
        nguess = 1
        self.guess = [ampguess, tauguess, doubleperiodguess, phaseoffsetguess, yoffset, nguess]
        self.set_bounds()

        return self.guess


class fit_exp_offset(GenericFit):
    '''
    calculate the exponential decay constant for experiemnts like T2, cpmg etc
    '''
    def __init__(self, data=None, xvals=None):
        super().__init__(data, xvals)

    def func(self):
        return 'amp * exp(-x/tau) + offset'

    def model(self, x, amp, tau, offset):
        func = amp * np.exp(-x/tau) + offset
        return func

    def get_guess(self):
        amp = np.max(self.data) - np.min(self.data)
        offset = np.mean(self.data)
        oneovere = (amp - offset)/np.exp(1)
        minfunc = self.data - oneovere
        indtau = np.argmin(np.abs(minfunc))
        tau = self.xvals[indtau]
        self.guess = [amp, tau, offset]
        return self.guess


class fit_exp(GenericFit):
    '''
    calculate the exponential decay constant for experiemnts like T2, cpmg etc
    '''

    def __init__(self, data=None, xvals=None):
        super().__init__(data, xvals)

    def func(self):
        return 'amp * exp(-x/tau)'

    def model(self, x, amp, tau):
        func = amp * np.exp(-x / tau)
        return func

    def get_guess(self):
        amp = np.max(self.data) - np.min(self.data)
        oneovere = amp / np.exp(1)
        minfunc = self.data - oneovere
        indtau = np.argmin(np.abs(minfunc))
        tau = self.xvals[indtau]
        self.guess = [amp, tau]
        return self.guess


class fit_power_offset(GenericFit):
    '''
    calculate the power law decay, start with initial guess of n=2
    '''
    def __init__(self, data=None, xvals=None):
        super().__init__(data, xvals)

    def model(self, x, amp, n, tau, offset):
        func = amp * np.exp(-(x/tau)**n) + offset
        return func

    def get_guess(self):
        amp = np.max(self.data) - np.min(self.data)
        n = 2       # start off with n=2, maybe loop over this and find best fit
        offset = 0      # assuming inv of 0 & 1 are being run in cpmg
        oneovere = (amp - offset)/np.exp(1)
        minfunc = self.data - oneovere
        indtau = np.argmin(np.abs(minfunc))
        tau = self.xvals[indtau]
        self.guess = [amp, n, tau, offset]
        return self.guess


class fit_power(GenericFit):
    '''
    calculate the power law decay, start with initial guess of n=2
    '''
    def __init__(self, data=None, xvals=None):
        super().__init__(data, xvals)

    def model(self, x, amp, tau, n):
        func = amp * np.exp(-(x/tau)**n)
        return func

    def get_guess(self):
        amp = np.max(self.data) - np.min(self.data)
        n = 2       # start off with n=2, maybe loop over this and find best fit
        oneovere = amp/np.exp(1)
        minfunc = self.data - oneovere
        indtau = np.argmin(np.abs(minfunc))
        tau = self.xvals[indtau]
        self.guess = [amp, tau, n]
        return self.guess


class fit_satcurve(GenericFit):
    '''
    for fitting PL saturation curve
    '''

    def __init__(self, data=None, xvals=None):
        super().__init__(data, xvals)

    def model(self, p, pl_sat, p_sat, bg):
        func = pl_sat * (p / p_sat) / (1 + (p / p_sat)) + p * bg
        return func

    def get_guess(self):
        pl_sat = np.max(self.data) / 2
        p_sat = np.mean(self.xvals)
        derivdata = np.squeeze(np.diff(self.data))
        derivxvals = np.squeeze(np.diff(self.xvals))
        bg = derivdata[-1] / derivxvals[-1]
        self.guess = [pl_sat, p_sat, abs(bg)]
        self.set_bounds()
        return self.guess

    def set_bounds(self, bounds=None):
        if bounds is None:
            bounds = ([0, 0, 0], [np.Inf, np.Inf, np.Inf])
        self.bounds = bounds


class fit_deerechosignal(GenericFit):
    '''
    from Mamin et al, PRB 2012
    Equation 7
    '''
    def __init__(self, data=None, xvals=None):
        super().__init__(data, xvals)

    def intermediatefunc(self, tau, tD, T1):
        '''
        dimensionless factor which for the case where the deer pulse aligns with the pi
        pulse on the NV, approaches 1 monotonically for for T1>>tau
        '''
        prefac = 2 * T1 / tau**2
        line1 = tau - 5*T1 + 4*T1*np.exp(-np.abs(tau/2-tD)/T1)
        line2_1 = -2 * T1 * np.exp(-(tau/2 + np.abs(tau/2 - tD))/T1)
        line2_2 = 2 * T1 * np.exp(-(tau/2 - np.abs(tau/2 - tD))/T1)
        line3 = T1 * np.exp(-tau/T1)
        retval = prefac * (line1 + line2_1 + line2_2 + line3)

        self.intfunc = retval

        return retval

    def alphabetatau(self, alpha0, beta0, tau, T2nv, n):
        '''
        Returns: alpha & b  eta as a function of tau
        This is for the most general use of the function as described in Mamin et al.
        Instead in the model here we take the min and max of data to set the y axis limits.
        alpha0: num photons counted per echo for NV in bright state
        beta0: num photons counted per echo for NV in dark state
        '''
        term1 = (alpha0 + beta0)/2
        term2_1 = (alpha0 - beta0)/2
        term2_2 = np.exp(-(tau/T2nv)**n)
        alpha = term1 + term2_1*term2_2
        beta = term1 - term2_1*term2_2
        return alpha, beta

    def model(self, tD, T1, Brms):
        '''
        Full generalized model is in the paper. We take the y axis limits to be purely set by the
        input data, instead of empirically calculated using the T2 and tau
        '''
        tau = 9.05e-6 # may want external set function for tau
        gamma = 2.8024e6 # for electron in units of Hz/Gauss
        intfunc = self.intermediatefunc(tau, tD, T1)
        maxval = max(self.data)
        minval = min(self.data)
        func = maxval*np.exp(-(gamma * Brms * tau)**2 * intfunc / 2) + minval
        return func

    def get_guess(self):
        self.bounds = ([1e-6, 0], [500e-6, .2])
        T1 = 100e-6
        Brms = 0.1
        self.guess = [T1, Brms]

        return self.guess


class fit_nvdepth(GenericFit):
    '''
    for fitting the NV depth from XY-8 measurements
    '''
    def __init__(self, data=None, xvals=None, infT2n=True, rep=1, rho=68):
        super().__init__(data, xvals)
        # infT2n = True if we want to assume inifnite nuclear T2
        self.infT2n = infT2n
        # number of XY-8 repetitions
        self.rep = rep
        self.rho = rho*(1e9)**3 # protons/cubic meter
        self.numpulses = rep*8  # for [XY-8]**rep sequence

    def model(self, tau, dnv, f_p):
        gamma_e = 2.802e6 * 1e4 # 1/s/T
        mu_0 = 4*np.pi*1e-7     # N/A**2
        hbar = 1.05e-34         # m**2 kg/s
        gamma_n = 2.68*1e8      # rad/s/T

        brms = np.sqrt(self.rho * (mu_0*hbar*gamma_n/4/np.pi)**2 * (5*np.pi/96/dnv**3))
        func = np.exp(-8 * (gamma_e*brms)**2 * self.kernel(tau, f_p))
        return func

    def kernel(self, tau, f_p):
        if self.infT2n:
            func = self.numpulses * tau * np.sinc((self.numpulses*tau*(f_p*2*np.pi - np.pi/tau)/2)/np.pi)
            func = func**2
        else:
            print('finite T2n is not implemented yet')
            func = 0
        return func

    def get_guess(self):
        omega_p = 840e3 * 2 * np.pi
        dnv = 15e-9
        self.guess = [dnv, omega_p]
        self.bounds = [(1e-9, 1e6), (30e-9, 10e6)]


class fit_xy8(GenericFit):
    '''
    for fitting XY8 contrast as a function of tau
    and extracting b_rms and larmor frequency
    '''
    def __init__(self, data=None, xvals=None, k=1):
        super().__init__(data,xvals)

        self.k = k

    def set_k(self, k):
        self.k = k

    def model(self, tau, b_rms, f_l):
        gam_e = 2.802e6 * 1e4  # Hz/T - this is actually gamma_e/2pi

        arg_sinc = 8 * self.k * tau / 2 * (2 * np.pi * f_l - np.pi / tau)
        knt = (8 * self.k * tau) ** 2 * (np.sin(arg_sinc) / arg_sinc) ** 2
        return np.exp(-8 * gam_e ** 2 * b_rms ** 2 * knt)


class fit_nvdepth_peace(fit_xy8):
    def __init__(self, data=None, xvals=None, k=1, rho=68):
        super().__init__(data, xvals, k)
        self.rho = rho

    def set_rho(self, rho):
        self.rho = rho

    def d2b(self, depth):
        mu0 = 4 * np.pi * 1e-7
        hbar = 1.0546 * 1e-34
        gam_n = 2.68 * 1e8
        d_nv = depth
        rho = self.rho*1e27
        b_rms = sqrt(rho * (mu0 * hbar * gam_n / 4 / np.pi) ** 2 * (5 * np.pi / 96 / d_nv ** 3))

        return b_rms

    def b2d(self, b_rms):
        mu0 = 4 * np.pi * 1e-7
        hbar = 1.0546 * 1e-34
        gam_n = 2.68 * 1e8
        rho = 68e27  # nm^-3

        d_nv = np.power((rho * (mu0 * hbar * gam_n / 4 / np.pi) ** 2 * (5 * np.pi / 96))/b_rms**2, 1.0/3)
        return d_nv

    # def set_guess(self, guess):
    #     # just guess depth and tau
    #     super().set_guess([self.d2b(guess[0]), (1.0/2/guess[1])])
    #
    # def set_bounds(self, bounds):
    #     super().set_bounds([self.d2b(bounds[0]), (1.0 / 2 / bounds[1])])

    def get_depth(self):
        return self.b2d(self.fp[0])*1e9


# class fit_rabi(GenericFit):
#     '''
#     used for fitting rabi oscillation data when many oscillations are present
#     uses a 2 component sinusoid model. this is very unstable currently with too
#     many fit parameters.
#     '''
#     def __init__(self, data, xvals=None):
#         super().__init__(data, xvals)
#
#     def model(self, x, amp, f1, phi1, f2, phi2, offset):
#         func = amp * np.sin(2*np.pi*x*f1 + phi1) * np.sin(2*np.pi*x*f2 + phi2) + offset
#         return func
#
#     def get_guess(self):
#         amp = .15
#         f1 = 10
#         phi1 = 0
#         f2 = 0.25
#         phi2 = 1.57
#         offset = 0.85
#         self.guess = [amp, f1, phi1, f2, phi2, offset]
#         return self.guess
#