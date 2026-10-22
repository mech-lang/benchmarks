"""Independent Python scalar reference for perturbed bounded systems."""
import math

SOLAR=4*math.pi*math.pi
YEAR=365.24

def system(seed):
    values=[
      [0,0,0,0,0,0,SOLAR],
      [4.84143144246472090,-1.16032004402742839,-.103622044471123109,.00166007664274403694*YEAR,.00769901118419740425*YEAR,-.0000690460016972063023*YEAR,.000954791938424326609*SOLAR],
      [8.34336671824457987,4.12479856412430479,-.403523417114321381,-.00276742510726862411*YEAR,.00499852801234917238*YEAR,.0000230417297573763929*YEAR,.000285885980666130812*SOLAR],
      [12.8943695621391310,-15.1111514016986312,-.223307578892655734,.00296460137564761618*YEAR,.00237847173959480950*YEAR,-.0000296589568540237556*YEAR,.0000436624404335156298*SOLAR],
      [15.3796971148509165,-25.9193146099879641,.179258772950371181,.00268067772490389322*YEAR,.00162824170038242295*YEAR,-.0000951592254519715870*YEAR,.0000515138902046611451*SOLAR]]
    for i,b in enumerate(values):
        for axis in range(3):
            b[axis]+=seed*.03*(i+1)*(axis+1)
            b[axis+3]+=.001*seed*(i-axis)
        if i:b[6]*=1+.01*seed*(i+1)
    for axis in range(3):
        momentum=0.
        for b in values:momentum+=b[axis+3]*b[6]
        values[0][axis+3]=-momentum/SOLAR
    return values

def integrate(seed,steps,dt):
    values=system(seed)
    for _ in range(steps):
        for i,a in enumerate(values):
            for b in values[i+1:]:
                dx=a[0]-b[0];dy=a[1]-b[1];dz=a[2]-b[2]
                squared=dx*dx+dy*dy+dz*dz
                magnitude=dt/(squared*math.sqrt(squared))
                first=a[6]*magnitude;second=b[6]*magnitude
                a[3]-=dx*second;a[4]-=dy*second;a[5]-=dz*second
                b[3]+=dx*first;b[4]+=dy*first;b[5]+=dz*first
        for b in values:
            for axis in range(3):b[axis]+=dt*b[axis+3]
    return values
