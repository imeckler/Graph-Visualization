# calculate coulomb's law force for the given parameters
def coulomb(dist_vect, k, q1, q2):
    return (k * q1 * q2 / ((dist_vect.length()+1) ** 2)) * dist_vect.normed()

# calculate the hooke's law force for the given parameters
def hooke(dist_vect, k, r):
    rest_vect = r * dist_vect.normed()
    return -k * (dist_vect - rest_vect)