# refer to http://www.glicko.net/glicko/glicko2.pdf

import math

class Player:
	_tau = 1
	_eps = 0.000001

	def __init__(self, rating = 1500, rd = 350, vol = 0.06):
		self.rating = rating
		self.rd = rd
		self.vol = vol

	def _rating_to_glicko2(self, r):
		return (r - 1500) / 173.7178

	def _rating_to_glicko(self, µ):
		return (µ * 173.7178) + 1500

	def _rd_to_glicko2(self, RD):
		return RD / 173.7178

	def _rd_to_glicko(self, φ):
		return φ * 173.7178

	def update_player(self, opponents):
		# players who did not compete need fewer calculations
		if not opponents:
			σ = self.vol
			φ = _rd_to_glicko2(self.rd)
			φ_prime = math.sqrt(φ**2 + σ**2)
			self.rd = _rd_to_glicko(φ_prime)
			return

		τ = self._tau
		σ = self.vol
		g = lambda φ: 1 / math.sqrt(1 + 3*φ**2 / math.pi**2)
		E = lambda µ, µ2, φ2: 1 / (1 + math.exp(-1 * g(φ2) * (µ - µ2)))

		# step 2
		µ = _rating_to_glicko2(self.rating)
		φ = _rd_to_glicko2(self.rd)

		# steps 3 and 4
		v_sum = 0
		∆_sum = 0
		for win, rating, rd in opponents:
			µ_j = _rating_to_glicko2(rating)
			φ_j = _rd_to_glicko2(rd)
			s_j = 1 if win else 0

			_E = E(µ, µ_j, φ_j)
			_g = g(φ_j)

			v_sum += _g**2 * _E * (1 - _E)
			∆_sum += _g * (s_j - _E)

		v = 1/v_sum
		∆ = v*∆_sum

		# step 5.1
		a = math.log(σ**2)
		ε = self._eps
		f = lambda x: (math.exp(x) * (∆**2 - φ**2 - v - math.exp(x)) / (2 * (φ**2 + v + math.exp(x))**2)) - (x-a)/τ**2

		# step 5.2
		A = a
		if ∆**2 > φ**2 + v:
			B = math.log(∆**2 - φ**2 - v)
		else:
			B = a - τ
			while f(B) < 0:
				B += τ

		# step 5.3
		f_A = f(A)
		f_B = f(B)

		# step 5.4
		while math.abs(B - A) > ε:
			C = A + (A - B)*f_A / (f_B - f_A)
			f_C = f(C)
			if f_C - f_B < 0:
				A = B
				f_A = f_B
			else:
				f_A /= 2
			B = C
			f_B = f_C

		# step 5.5
		σ_prime = math.exp(A/2)

		# step 6
		φ_star = math.sqrt(φ**2 + σ_prime**2)

		# step 7
		φ_prime = 1 / math.sqrt(1/φ_star**2 + 1/v)
		µ_prime = µ + φ_prime * ∆_sum

		# step 8
		self.rating = _rating_to_glicko(µ_prime)
		self.rd = _rd_to_glicko(φ_prime)

	def __repr__(self):
	  return "R:\t" + str(self.getRating()) + "\nRD:\t" + str(self.getRd()) + "\nVol:\t" + str(self.getVol())

	def __str__(self):
	  return self.__repr__()
