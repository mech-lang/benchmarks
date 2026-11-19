"""Task definitions independent of Mech's compiler, scheduler and storage representation."""
import math


def table_join(operation, key):
    left = [(key, 10.0), (key, 11.0), (2.0, 12.0), (3.0, 13.0)]
    right = [(1.0, 20.0), (1.0, 21.0), (2.0, 22.0), (4.0, 23.0)]
    rows = []
    matched_right = set()
    for k, payload in left:
        matches = [(j, r) for j, (rk, r) in enumerate(right) if k == rk]
        if operation == 'left-semi-join':
            if matches: rows.append([k, payload])
            continue
        if operation == 'left-anti-join':
            if not matches: rows.append([k, payload])
            continue
        for j, r in matches:
            rows.append([k, payload, r])
            matched_right.add(j)
        if not matches and operation in ('left-outer-join', 'full-outer-join'):
            rows.append([k, payload, None])
    if operation in ('right-outer-join', 'full-outer-join'):
        rows.extend([k, None, payload] for j, (k, payload) in enumerate(right) if j not in matched_right)
    columns = ['key', 'left'] if operation in ('left-semi-join', 'left-anti-join') else ['key', 'left', 'right']
    return {'kind':'table', 'columns':columns, 'rows':rows}


def graph(bridge):
    # Independent edge-list propagation, not a matrix product.
    edges = [(i, i, 1.0) for i in range(8)] + [(0,1,2.0)]
    edges += [(a,b,1.0) for a,b in [(1,2),(2,3),(3,1),(4,5),(5,6),(6,7)]]
    edges += [(3,4,bridge)]
    counts = [1.0] + [0.0]*7
    for _ in range(7):
        following = [0.0]*8
        for a,b,multiplicity in edges:
            following[b] += counts[a]*multiplicity
        counts = following
    return {'kind':'matrix', 'shape':[8,1], 'values':counts}


def transpose(a):
    return [list(column) for column in zip(*a)]


def multiply(a, b):
    return [[sum(x*y for x,y in zip(row,column)) for column in zip(*b)] for row in a]


def add(a, b):
    return [[x+y for x,y in zip(ar,br)] for ar,br in zip(a,b)]


def ekf(schedule, count):
    """Conventional row-major EKF with Joseph update; no Mech kernels invoked."""
    state = [2.0,1.0,0.15]
    covariance = [[1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,0.05]]
    noise = [[0.25,0.0],[0.0,0.0009]]
    process = [[0.04,0.0],[0.0,0.0025]]
    identity = [[float(i==j) for j in range(3)] for i in range(3)]
    result = []
    for i in range(count):
        speed, yaw, distance, bearing = schedule[i % len(schedule)]
        co, si, dt = math.cos(state[2]), math.sin(state[2]), 0.05
        motion = [[1.0,0.0,-speed*si*dt],[0.0,1.0,speed*co*dt],[0.0,0.0,1.0]]
        control = [[co*dt,0.0],[si*dt,0.0],[0.0,dt]]
        predicted = [state[0]+speed*co*dt,state[1]+speed*si*dt,state[2]+yaw*dt]
        p = add(multiply(multiply(motion,covariance),transpose(motion)), multiply(multiply(control,process),transpose(control)))
        dx,dy = 25.0-predicted[0],-10.0-predicted[1]
        q = dx*dx+dy*dy
        r = math.sqrt(q)
        h = [[-dx/r,-dy/r,0.0],[dy/q,-dx/q,-1.0]]
        innovation = [[distance-r],[bearing-(math.atan2(dy,dx)-predicted[2])]]
        s = add(multiply(multiply(h,p),transpose(h)),noise)
        determinant = s[0][0]*s[1][1]-s[0][1]*s[1][0]
        inverse = [[s[1][1]/determinant,-s[0][1]/determinant],[-s[1][0]/determinant,s[0][0]/determinant]]
        gain = multiply(multiply(p,transpose(h)),inverse)
        correction = multiply(gain,innovation)
        state = [x+v[0] for x,v in zip(predicted,correction)]
        kh = multiply(gain,h)
        a = [[x-y for x,y in zip(ir,kr)] for ir,kr in zip(identity,kh)]
        joseph = add(multiply(multiply(a,p),transpose(a)),multiply(multiply(gain,noise),transpose(gain)))
        covariance = [[0.5*(joseph[i][j]+joseph[j][i]) for j in range(3)] for i in range(3)]
        values = state + [v for row in covariance for v in row]
        if not all(math.isfinite(v) for v in values) or min(covariance[i][i] for i in range(3))<=0:
            raise ValueError('invalid oracle EKF covariance')
        result.append({'kind':'matrix','shape':[1,12],'values':values})
    return result
