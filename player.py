from imports import *
from bot import Bot

def solve_quadratic(a, b, c):
    """
    Solves a quadratic equation of the form ax² + bx + c = 0.

    Args:
        a: The coefficient of x².
        b: The coefficient of x.
        c: The constant term.

    Returns:
        A tuple containing the two roots of the equation.
    """
    delta = (b**2) - 4*(a*c)

    if delta >= 0:
        # Real roots
        x1 = (-b - delta**0.5) / (2*a)
        x2 = (-b + delta**0.5) / (2*a)
    else:
        # Complex roots
        x1 = -1
        x2 = -1
    print(delta, x1, x2)

    if x1 >= 0:
        return x1
    if x2 >= 0:
        return x2
    return -1

class Player(Bot):
    def __init__(self):
        super().__init__()
        self.actions = ActionChains(self.driver)
        self.reset()

    def reset(self):
        self.screenshot = None
        self.player_cords = None
        self.safe_platform_colors = [(255, 252, 229), (229, 255, 230), (231, 237, 255)]
        self.monster_colors = [(73, 0, 64), (216, 216, 216), (255, 179, 137)]
        self.monsters = []
        self.player_color = (37, 70, 229)
        self.safe_platforms = []
        self.horizontal_speed = 210  # About that number
        self.jump_height = 120  # About that number
        self.jump_force = 385  # About that number
        self.gravity = 592  # About that number
        self.prev_player_cords = (0, 0)
        self.prev_velocity = (0, 0)
        self.velocity = None
        self.canvas = self.driver.find_element(By.TAG_NAME, "canvas")
        self.standing_platform = None
        self.jumped = False
        self.just_moved = False
        self.to_skip = 0

    def move(self, x):
        x /= self.horizontal_speed
        if x > 0:
            self.actions.key_down(Keys.ARROW_RIGHT)
            self.actions.pause(x)
            self.actions.key_up(Keys.ARROW_RIGHT)
            self.actions.perform()
        else:
            x = -x
            self.actions.key_down(Keys.ARROW_LEFT)
            self.actions.pause(x)
            self.actions.key_up(Keys.ARROW_LEFT)
            self.actions.perform()

    def update_screenshot(self):

        png_data = self.driver.get_screenshot_as_png()
        self.screenshot = cv2.imdecode(np.frombuffer(png_data, dtype=np.uint8, ), cv2.IMREAD_COLOR, )
        cv2.imwrite("screenshot.png", self.screenshot)

    def detect_objects(self):
        def detect_player():
            self.player_cords = None
            mask = cv2.inRange(self.screenshot, self.player_color, self.player_color)
            coordinates = cv2.findNonZero(mask)
            if coordinates is not None:
                for contour in coordinates:
                        for u in contour:
                            x, y = u
                            if self.player_cords == None or (x, -y) < self.player_cords:
                                self.player_cords = (x, y, 0, 0)
                self.player_cords = (self.player_cords[0] + 7, self.player_cords[1] + 8, 0, 0)
                self.player_cords = (self.player_cords[0], self.player_cords[1], self.player_cords[0] + 14, self.player_cords[1] - 37)


        def detect_safe_platforms():
            self.safe_platforms = []
            for safe_platform_color in self.safe_platform_colors:
                mask = cv2.inRange(self.screenshot, safe_platform_color, safe_platform_color)
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)


                for contour in contours:
                    x, y, w, h = cv2.boundingRect(contour)
                    y -= 2 # adjust the y-coordinate to account for the top of the platform
                    if h >= 15:
                        self.safe_platforms.append((x, y, x + w, y + h))
                        #cv2.rectangle(self.screenshot, (x, y), (x + w, y + h), (0, 0, 255), 2)
                #cv2.imshow("", self.screenshot)
                #cv2.waitKey(1)

        def detect_monsters():
            self.monsters = []
            for monster_color in self.monster_colors:
                mask = cv2.inRange(self.screenshot, monster_color, monster_color)
                coordinates = cv2.findNonZero(mask)
                monster_cords = (0, 0)
                n = 0
                if coordinates is not None:
                    for contour in coordinates:
                        for u in contour:
                            x, y = u
                            monster_cords = (monster_cords[0] + x, monster_cords[1] + y)
                            n += 1
                if n >= 100:
                    #print(n)
                    monster_cords = (monster_cords[0] // n, monster_cords[1] // n)
                    monster_cords = (monster_cords[0] - 30, monster_cords[1] - 30, monster_cords[0] + 30, monster_cords[1] + 30)
                    cv2.rectangle(self.screenshot, (monster_cords[0], monster_cords[1]), (monster_cords[2], monster_cords[3]), (0, 0, 255), 2)
                    self.monsters.append(monster_cords)


        detect_player()
        detect_safe_platforms()
        detect_monsters()


    def update_standing_platform(self):
        self.standing_platform = None
        if not self.player_cords:
            return
        for platform in self.safe_platforms:

            if platform[0] <= self.player_cords[2] + 3 and platform[2] >= self.player_cords[0] - 3:
                if platform[1] > self.player_cords[1]:
                    if self.standing_platform is None or platform[1] < self.standing_platform[1]:
                        self.standing_platform = platform
        return
    def retry_if_lost(self):
        if np.array_equal(self.screenshot[357, 580], (93, 137, 253)):
            print("Lost, retrying...")
            mouse.move(-1000000, -1000000)
            mouse.move(500, 285)
            mouse.click()
            time.sleep(1)
            self.reset()
            return True

    def is_place_dangerous(self, place, monster, threshold):
        if monster[1] <= place[1] and monster[3] >= place[3] - self.jump_height:
            if min(abs(monster[0] - place[0]), abs(monster[2] - place[0])) <= threshold:
                return True
        return False

    def play(self):
        self.move(0)
        time.sleep(1)

        while True:
            self.game_cycle()

    def game_cycle(self):
        start = time.time()
        self.update_screenshot()
        self.detect_objects()
        if self.retry_if_lost():
            return
        if not self.player_cords:
            return
        self.update_standing_platform()
        self.velocity = (self.player_cords[0] - self.prev_player_cords[0], self.player_cords[1] - self.prev_player_cords[1])
        self.prev_player_cords = self.player_cords
        delta_time = time.time() - start
        if self.velocity[1] > 0 and self.standing_platform:
            # (self.standing_platform[1] - self.player_cords[1]) = self.velocity * t + self.gravity * t * t / 2
            new_time = solve_quadratic(self.gravity / 2, self.velocity[1], self.player_cords[1] - self.standing_platform[1]) - 0.1
            if new_time >= delta_time:
                time.sleep(new_time - delta_time)
                delta_time = new_time
                print("Jumped!")
                cv2.imwrite("screenshot2.png", self.screenshot)
                self.jumped = True
        self.player_cords = (self.player_cords[0] + self.velocity[0] * delta_time, self.player_cords[1] + self.velocity[1] * delta_time)
        if self.standing_platform:
            if self.player_cords[1] > self.standing_platform[1]:
                self.player_cords = (self.player_cords[0], self.standing_platform[1] - (self.player_cords[1] - self.standing_platform[1]))
                self.velocity = (self.velocity[0], self.velocity[1] + self.jump_force)
        self.player_cords = (self.player_cords[0], self.player_cords[1] + self.gravity * delta_time * delta_time / 2)



        self.prev_velocity = self.velocity
        self.player_cords = (self.player_cords[0], self.player_cords[1], self.player_cords[0] + 14, self.player_cords[1] - 37)
        if self.to_skip > 0:
            self.to_skip -= 1
            return

        if not self.player_cords:
            # Player not found, wait for it to appear
            return

        are_we_safe = True
        for monster in self.monsters:
            if self.is_place_dangerous(self.player_cords, monster, 500):
                are_we_safe = False
                break

        self.safe_platforms.sort(key=lambda x: [x[1], abs(x[0] - self.player_cords[0])])
        for platform in self.safe_platforms:
            target = 0
            left = 230
            right = 708
            mid = (left + right) // 2
            if platform[0] + 20 <= mid <= platform[2] - 20:
                target = mid
            elif platform[2] - 20 < mid:
                target = platform[2] - 20
            else:
                target = platform[0] + 20
            if self.standing_platform and self.standing_platform[1] > platform[1]:
                height = platform[1] - self.player_cords[1]
                # t * self.velocity[1] + t * t / 2 * self.gravity - y_dist = 0
                # height = self.velocity[1] * t + self.gravity / 2 * t * t
                t = solve_quadratic(self.gravity / 2, self.velocity[1], -height)
                if t == -1:
                    print(self.gravity / 2)
                    print(self.velocity[1])
                    print(-height)
                    exit(1)
                max_x_dist = t * self.horizontal_speed
                print(max_x_dist, abs(self.player_cords[0] - platform[2]))
                if abs(self.player_cords[0] - platform[0]) <= max_x_dist or abs(self.player_cords[0] - platform[2]) <= max_x_dist:
                    if self.jumped or not are_we_safe:
                        if self.standing_platform[1] - platform[1] <= self.jump_height:
                            platform_is_safe = True
                            for monster in self.monsters:
                                if self.is_place_dangerous((target, platform[1], self.player_cords[2], self.player_cords[3]), monster, 200):
                                    platform_is_safe = False
                                    break
                            if len(self.monsters) == 3:
                                platform_is_safe = True
                            if platform_is_safe or not are_we_safe:
                                print("Moved to", target, platform, self.standing_platform, self.standing_platform[1] - platform[1])
                                self.move(target - self.player_cords[0])
                                cv2.rectangle(self.screenshot, (platform[0], platform[1]), (platform[2], platform[3]), (0, 255, 0), 2)

                                self.jumped = False
                                self.to_skip = 0
                                break
        if self.standing_platform:
            cv2.rectangle(self.screenshot, (self.standing_platform[0], self.standing_platform[1]), (self.standing_platform[2], self.standing_platform[3]), (255, 0, 0), 2)
        cv2.imshow("", self.screenshot)
        cv2.waitKey(1)





player = Player()
player.play()
