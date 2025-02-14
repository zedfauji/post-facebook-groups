from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random

def post_in_groups(self):
    """ Publish each post in each group from data file """

    selectors = {
        "display_input": ".x6s0dn4.x78zum5.x1l90r2v.x1pi30zi.x1swvt13.xz9dl7a > span.x1emribx + div.x1i10hfl",
        "input": 'div.notranslate._5rpu[role="textbox"]',
        "show_image_input": '[aria-label="Photo/video"]',
        "add_image": 'input[type="file"][accept^="image/*"]',
        "submit": '[aria-label="Post"][role="button"], [aria-label="Publicar"][role="button"]',
    }

    posts_done = []
    failed_groups = []

    for group in self.json_data["groups"]:
        logger.info(f"Processing group: {group}")

        try:
            self.set_page(group)

            # Wait for the input box to appear
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selectors["display_input"]))
            )

            # Get random post
            post = random.choice(self.json_data["posts"])
            post_text = post["text"]
            post_image = post.get("image", "")

            # Open text input
            try:
                input_box = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selectors["display_input"]))
                )
                input_box.click()
                logger.info(f"Opened text input successfully in group: {group}")

                # Wait for text input box to load
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selectors["input"]))
                )

                time.sleep(2)  # Small wait after clicking to stabilize

            except Exception as e:
                logger.error(f"Failed to open text input in group {group}: {e}")
                failed_groups.append(group)
                continue

            # Write text
            try:
                text_input = self.driver.find_element(By.CSS_SELECTOR, selectors["input"])
                text_input.send_keys(post_text)
                logger.info(f"Successfully wrote text in group: {group}")
            except Exception as e:
                logger.error(f'Error writing text "{post_text}" in group {group}: {e}')
                failed_groups.append(group)
                continue

            # Upload image if present
            if post_image:
                try:
                    image_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selectors["show_image_input"]))
                    )
                    image_btn.click()
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selectors["add_image"]))
                    )
                    self.send_data(selectors["add_image"], post_image)
                    logger.info(f"Image uploaded successfully in group: {group}")
                except Exception as e:
                    logger.error(f"Failed to upload image in group {group}: {e}")
                    failed_groups.append(group)
                    continue

            # Submit post
            try:
                submit_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selectors["submit"]))
                )
                logger.info(f"Found Post button in group: {group}")

                # First try normal click
                submit_btn.click()
                logger.info(f"Clicked 'Post' button in group: {group}")

                # If button is still visible, use JavaScript click
                time.sleep(3)  # Allow UI to process click
                if submit_btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", submit_btn)
                    logger.info(f"Clicked 'Post' button using JavaScript in group: {group}")

                # 🔴 FIX: Wait until post is fully submitted
                WebDriverWait(self.driver, 10).until(
                    EC.invisibility_of_element((By.CSS_SELECTOR, selectors["submit"]))
                )
                
                logger.info(f'Post published successfully in group: {group}')
                posts_done.append({"group": group, "post": post})

            except Exception as e:
                logger.error(f"Failed to submit post in group {group}: {e}")
                failed_groups.append(group)
                continue

            # 🔴 FIX: Extra wait after posting before switching groups
            time.sleep(5)

        except Exception as e:
            logger.error(f"Unexpected error in group {group}: {e}")
            failed_groups.append(group)

    logger.info(f"Posting completed. Successful posts: {len(posts_done)}, Failed groups: {len(failed_groups)}")
    if failed_groups:
        logger.warning(f"Failed to post in groups: {failed_groups}")
